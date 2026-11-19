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

    // view orientation set by hand, kept as one quaternion so a drag in any direction (diagonals included) turns the scene
    // about the axis perpendicular to that drag, like grabbing a globe. Head turning still works as usual on top of this.
    private var view: Quaternion = Quaternion.Identity
    /** 수평 유지: after every move remove the sideways tilt (roll) seen from the front, so the horizon stays level */
    var keepLevel = false
    private var dragFrom: Vector3? = null
    private var dragStart: Vector3? = null
    /** a pinch on the 360 scene without dragging (used to bring the hidden control panel back) */
    var onTap: () -> Unit = {}

    /** dYaw: degrees about the vertical axis (+ turns the view right), dPitch: degrees about the left-right axis (+ moves the scene up).
     *  Both at once give a single diagonal rotation. */
    fun rotateBy(dYaw: Float, dPitch: Float) {
        val ang = kotlin.math.sqrt(dYaw * dYaw + dPitch * dPitch)
        if (ang < 1e-3f) return
        val axis = (Vector3.Up * dYaw + Vector3.Right * dPitch) / ang
        view = norm(Quaternion.fromAxisAngle(axis, ang) * view)
        settle()
    }

    /** 30 degree steps turn the scene about its own vertical pole (a turntable), whatever the tilt */
    fun turn(deg: Float) { view = norm(view * Quaternion.fromAxisAngle(Vector3.Up, deg)); settle() }

    fun resetView() { view = Quaternion.Identity; applyView() }

    /** one-shot: straighten the horizon, keeping where the scene points */
    fun levelNow() { view = removeRoll(view); applyView() }

    private fun settle() { if (keepLevel) view = removeRoll(view); applyView() }

    private fun removeRoll(q: Quaternion): Quaternion {
        val u = q * Vector3.Up                                    // the scene's "up" as seen by the viewer
        if (u.x * u.x + u.y * u.y < 0.02f) return q               // looking straight at a pole: roll is undefined
        val phi = Math.toDegrees(Math.atan2(u.x.toDouble(), u.y.toDouble())).toFloat()
        return norm(Quaternion.fromAxisAngle(Vector3.Backward, phi) * q)
    }

    private fun norm(q: Quaternion): Quaternion {
        val n = kotlin.math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w)
        return if (n < 1e-6f) Quaternion.Identity else Quaternion(q.x / n, q.y / n, q.z / n, q.w / n)
    }

    private fun applyView() { entity?.setPose(Pose(Vector3(0f, 0f, 0f), view)) }

    /** pinch on the sphere and drag in any direction: the point under the hand follows the hand (grab-and-turn). */
    private fun onSphereInput(ev: InputEvent) {
        when (ev.action) {
            InputEvent.Action.DOWN -> { dragFrom = ev.direction.toNormalized(); dragStart = dragFrom }
            InputEvent.Action.MOVE -> {
                val a = dragFrom ?: return
                val b = ev.direction.toNormalized()
                val axis = a cross b
                val len = kotlin.math.sqrt(axis.x * axis.x + axis.y * axis.y + axis.z * axis.z)
                if (len > 1e-5f) {
                    val ang = Math.toDegrees(Math.atan2(len.toDouble(), (a dot b).toDouble())).toFloat() * DRAG_GAIN
                    view = norm(Quaternion.fromAxisAngle(axis / len, ang) * view)
                    settle()
                }
                dragFrom = b
            }
            InputEvent.Action.UP -> {
                val a = dragStart; val b = ev.direction.toNormalized()
                if (a != null && (a dot b) > 0.9995f) onTap()          // moved less than ~1.8 degrees: a tap
                dragFrom = null; dragStart = null
            }
            InputEvent.Action.CANCEL -> { dragFrom = null; dragStart = null }
        }
    }

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
        view = Quaternion.Identity; applyView()   // every item starts facing its front
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
                    override fun onPlaybackStateChanged(state: Int) { if (state == Player.STATE_ENDED) { p.seekTo(0); p.play() } }
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
                    p.addListener(object : Player.Listener {
                        override fun onPlaybackStateChanged(state: Int) { if (state == Player.STATE_ENDED) { p.seekTo(0); p.play() } }
                    })
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
