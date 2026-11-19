package com.panocalm.xr

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Rect
import android.net.Uri
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.DefaultRenderersFactory
import androidx.media3.exoplayer.ExoPlayer
import androidx.xr.runtime.Session
import androidx.xr.runtime.math.IntSize2d
import androidx.xr.runtime.math.Pose
import androidx.xr.runtime.math.Quaternion
import androidx.xr.runtime.math.Vector3
import androidx.xr.scenecore.InputEvent
import androidx.xr.scenecore.InteractableComponent
import androidx.xr.scenecore.ExperimentalSurfaceEntityPixelDimensionsApi
import androidx.xr.scenecore.SpatialCapability
import androidx.xr.scenecore.SurfaceEntity
import androidx.xr.scenecore.scene
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Shows one equirectangular item on a SurfaceEntity sphere around the user (Full Space).
 * Video: ExoPlayer (HEVC, hardware decode) renders straight into the sphere surface, looping.
 * Photo: the decoded bitmap is drawn once into the sphere surface with a hardware canvas.
 * A new SurfaceEntity is created per item (a Surface accepts only one producer), the old one is disposed.
 */
class SphereViewer(private val ctx: Context, private val session: Session, private val scope: CoroutineScope) {
    private var entity: SurfaceEntity? = null
    private var player: ExoPlayer? = null
    private var job: Job? = null
    var onError: (String) -> Unit = {}

    // view direction set by hand: yaw turns the sphere left/right, pitch tilts it up/down (head turning still works as usual)
    var yawDeg = 0f; private set
    var pitchDeg = 0f; private set
    var onViewChanged: (Float, Float) -> Unit = { _, _ -> }
    private var dragFrom: Vector3? = null

    fun rotateBy(dYaw: Float, dPitch: Float) {
        yawDeg = ((yawDeg + dYaw) % 360f + 360f) % 360f
        pitchDeg = (pitchDeg + dPitch).coerceIn(-90f, 90f)
        applyView(); onViewChanged(yawDeg, pitchDeg)
    }

    fun resetView() { yawDeg = 0f; pitchDeg = 0f; applyView(); onViewChanged(0f, 0f) }

    private fun applyView() {
        // like a 360 viewer camera: turn the scene around its own vertical pole (yaw), then tilt it about the viewer's
        // left-right axis (pitch). Rx * Ry keeps the horizon level for any yaw; Ry * Rx would turn the tilt into a roll after turning.
        val q = Quaternion.fromAxisAngle(Vector3.Right, pitchDeg) * Quaternion.fromAxisAngle(Vector3.Up, yawDeg)
        entity?.setPose(Pose(Vector3(0f, 0f, 0f), q))
    }

    /** pinch on the sphere and drag: the scene follows the hand (grab-and-turn). */
    private fun onSphereInput(ev: InputEvent) {
        when (ev.action) {
            InputEvent.Action.DOWN -> dragFrom = ev.direction
            InputEvent.Action.MOVE -> {
                val a = dragFrom ?: return
                val b = ev.direction
                val dYaw = Math.toDegrees(Math.atan2(b.x.toDouble(), -b.z.toDouble()) - Math.atan2(a.x.toDouble(), -a.z.toDouble())).toFloat()
                val dPitch = Math.toDegrees(Math.asin(b.y.toDouble().coerceIn(-1.0, 1.0)) - Math.asin(a.y.toDouble().coerceIn(-1.0, 1.0))).toFloat()
                rotateBy(-wrap(dYaw) * DRAG_GAIN, dPitch * DRAG_GAIN)
                dragFrom = b
            }
            InputEvent.Action.UP, InputEvent.Action.CANCEL -> dragFrom = null
        }
    }

    private fun wrap(d: Float): Float = if (d > 180f) d - 360f else if (d < -180f) d + 360f else d

    val isPlaying: Boolean get() = player?.isPlaying == true
    val isShowing: Boolean get() = entity != null

    fun enterImmersive() {
        session.scene.requestFullSpaceMode()
        if (SpatialCapability.PASSTHROUGH_CONTROL in session.scene.spatialCapabilities) {
            session.scene.spatialEnvironment.preferredPassthroughOpacity = 0f
        }
    }

    fun exitImmersive() {
        close()
        session.scene.spatialEnvironment.preferredPassthroughOpacity = SpatialEnvironmentNoPreference
        session.scene.requestHomeSpaceMode()
    }

    @OptIn(ExperimentalSurfaceEntityPixelDimensionsApi::class)
    fun show(item: Item) {
        close()
        val e = SurfaceEntity.create(
            session = session,
            pose = Pose.Identity,
            shape = SurfaceEntity.Shape.Sphere(RADIUS_M),
            stereoMode = SurfaceEntity.StereoMode.MONO,
            parent = session.scene.activitySpace,
        )
        entity = e
        yawDeg = 0f; pitchDeg = 0f; applyView(); onViewChanged(0f, 0f)   // every item starts facing its front
        try { e.addComponent(InteractableComponent.create(session) { ev -> onSphereInput(ev) }) } catch (t: Throwable) { /* drag pad on the panel still works */ }
        when (item.kind) {
            Item.Kind.VIDEO -> {
                val rf = DefaultRenderersFactory(ctx).setEnableDecoderFallback(true)
                val p = ExoPlayer.Builder(ctx, rf).build()
                p.repeatMode = Player.REPEAT_MODE_ONE
                p.videoScalingMode = C.VIDEO_SCALING_MODE_SCALE_TO_FIT
                p.setVideoSurface(e.getSurface())
                p.setMediaItem(MediaItem.fromUri(item.uri))
                p.addListener(object : Player.Listener {
                    override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                        onError("재생 오류: ${error.errorCodeName}")
                    }
                })
                p.prepare(); p.play()
                player = p
            }
            Item.Kind.PHOTO -> {
                item.audio?.let { a ->                 // looping ambience while the photo is shown
                    val p = ExoPlayer.Builder(ctx).build()
                    p.repeatMode = Player.REPEAT_MODE_ONE
                    p.setMediaItem(MediaItem.fromUri(a))
                    p.prepare(); p.play()
                    player = p
                }
                e.setSurfacePixelDimensions(IntSize2d(item.width, item.height))
                job = scope.launch {
                    val bmp = withContext(Dispatchers.IO) { decode(item) }
                    if (bmp == null) { onError("사진을 열지 못했습니다"); return@launch }
                    if (entity !== e) return@launch
                    val surface = e.getSurface()
                    val canvas = surface.lockHardwareCanvas()
                    try {
                        canvas.drawBitmap(bmp, null, Rect(0, 0, canvas.width, canvas.height), null)
                    } finally {
                        surface.unlockCanvasAndPost(canvas)
                    }
                }
            }
        }
    }

    fun togglePause() {
        val p = player ?: return
        if (p.isPlaying) p.pause() else p.play()
    }

    fun close() {
        job?.cancel(); job = null
        player?.release(); player = null
        entity?.dispose(); entity = null
    }

    private fun decode(item: Item): Bitmap? {
        val o = BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.HARDWARE }
        return try { ctx.contentResolver.openInputStream(item.uri)?.use { BitmapFactory.decodeStream(it, null, o) } } catch (e: Exception) { null }
    }

    companion object {
        const val RADIUS_M = 20f
        const val DRAG_GAIN = 1.5f
        /** SpatialEnvironment.NO_PASSTHROUGH_OPACITY_PREFERENCE: hand passthrough back to the system. */
        val SpatialEnvironmentNoPreference: Float = androidx.xr.scenecore.SpatialEnvironment.NO_PASSTHROUGH_OPACITY_PREFERENCE
    }
}
