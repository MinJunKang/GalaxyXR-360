package com.panocalm.xr

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Rect
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.os.PowerManager
import java.io.File
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
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
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

    // photo ambience: framework MediaPlayer with native looping, played from a private copy of the file (no content-provider
    // seeking on every loop). A watchdog restarts any sound/video that stopped without the user pausing it.
    private var amb: PcmLoop? = null
    private var ambFile: File? = null
    private var userPaused = false
    private var watchdog: Job? = null
    private var videoUri: Uri? = null
    private var videoLoops = 0
    private var lastPos = -1L
    private var stuckMs = 0L
    private var startedAt = 0L
    private var recoveries = 0
    /** one line for the control bar: is the sound/video running, for how long, how often it had to be restarted */
    var onPlayInfo: (String) -> Unit = {}

    // view orientation set by hand, kept as one quaternion so a drag in any direction (diagonals included) turns the scene
    // about the axis perpendicular to that drag, like grabbing a globe. Head turning still works as usual on top of this.
    private var view: Quaternion = Quaternion.Identity
    /** 수평 유지: after every move remove the sideways tilt (roll) seen from the front, so the horizon stays level */
    var keepLevel = true
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
        userPaused = false; recoveries = 0; videoLoops = 0; startedAt = System.currentTimeMillis()
        startWatchdog()
        when (item.kind) {
            Item.Kind.VIDEO -> { videoUri = item.uri; startVideo(e, item.uri) }
            Item.Kind.PHOTO -> {
                item.audio?.let { a ->                 // looping ambience while the photo is shown
                    scope.launch {
                        val f = withContext(Dispatchers.IO) { cacheAudio(a) }
                        if (entity !== e) return@launch
                        if (f == null) { onPlayInfo("🔇 소리 파일을 열지 못했습니다"); return@launch }
                        ambFile = f
                        val loop = try { withContext(Dispatchers.IO) { PcmLoop.start(f) } } catch (t: Throwable) {
                            onPlayInfo("🔇 소리를 열지 못했습니다: ${t.message}"); return@launch
                        }
                        if (entity !== e) { loop.release(); return@launch }
                        if (userPaused) loop.pause()
                        amb = loop
                    }
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
        userPaused = !userPaused
        player?.let { if (userPaused) it.pause() else it.play() }
        amb?.let { if (userPaused) it.pause() else it.resume() }
    }

    /** ExoPlayer straight into the sphere surface, looping. A loop is counted for the status line; if playback stops moving
     *  (seen on the headset after the first pass), the watchdog first seeks back to 0, and on the next stall rebuilds the player. */
    private fun startVideo(e: SurfaceEntity, uri: Uri) {
        player?.release()
        val rf = DefaultRenderersFactory(ctx).setEnableDecoderFallback(true)
        val p = ExoPlayer.Builder(ctx, rf).build()
        p.repeatMode = Player.REPEAT_MODE_ONE
        p.videoScalingMode = C.VIDEO_SCALING_MODE_SCALE_TO_FIT
        p.setVideoSurface(e.getSurface())
        p.setMediaItem(MediaItem.fromUri(uri))
        p.addListener(object : Player.Listener {
            override fun onMediaItemTransition(mediaItem: MediaItem?, reason: Int) {
                if (reason == Player.MEDIA_ITEM_TRANSITION_REASON_REPEAT) videoLoops++
            }
            override fun onPlaybackStateChanged(state: Int) { if (state == Player.STATE_ENDED && !userPaused) { videoLoops++; p.seekTo(0); p.play() } }
            override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                onPlayInfo("재생 오류: ${error.errorCodeName} → 다시 시작"); stuckMs = 10_000L    // let the watchdog rebuild now
            }
        })
        p.setWakeMode(C.WAKE_MODE_LOCAL)
        p.prepare(); p.play()
        player = p; lastPos = -1L; stuckMs = 0L
    }

    /** copies the (small) sound file into the app cache once, so looping never depends on the Downloads provider */
    private fun cacheAudio(u: Uri): File? = try {
        val dir = File(ctx.cacheDir, "audio").apply { mkdirs() }
        val f = File(dir, Integer.toHexString(u.toString().hashCode()) + ".m4a")
        if (!f.exists() || f.length() == 0L) {
            val tmp = File(dir, f.name + ".tmp")
            ctx.contentResolver.openInputStream(u)?.use { i -> tmp.outputStream().use { o -> i.copyTo(o) } } ?: throw IllegalStateException("no stream")
            tmp.renameTo(f)
        }
        f
    } catch (e: Exception) { null }

    private fun startWatchdog() {
        watchdog?.cancel()
        watchdog = scope.launch {
            while (isActive) {
                delay(2000)
                if (entity == null) break
                val p = player; val m = amb
                if (!userPaused) {
                    if (p != null) {
                        val pos = p.currentPosition
                        stuckMs = if (pos == lastPos || !p.isPlaying) stuckMs + 2000 else 0
                        lastPos = pos
                        if (stuckMs >= 4000) {                       // not moving for 4 s, whatever the state says
                            recoveries++; stuckMs = 0
                            val e = entity; val u = videoUri
                            if (recoveries % 2 == 0 && e != null && u != null) startVideo(e, u)
                            else { if (p.playbackState == Player.STATE_IDLE) p.prepare(); p.seekTo(0); p.play() }
                        }
                    }
                    if (m != null && !m.isPlaying) { recoveries++; m.resume() }
                }
                val sec = (System.currentTimeMillis() - startedAt) / 1000
                val what = if (p != null) "▶ 영상(${videoLoops + 1}번째)" else if (m != null) "🔊 소리(${m.passes + 1}번째)" else ""
                if (what.isNotEmpty()) onPlayInfo("$what " + (if (userPaused) "일시정지" else "재생 중") +
                    " · ${sec / 60}:${"%02d".format(sec % 60)}" + (if (recoveries > 0) " · 자동 재시작 ${recoveries}회" else ""))
            }
        }
    }

    fun close() {
        job?.cancel(); job = null
        watchdog?.cancel(); watchdog = null
        player?.release(); player = null
        amb?.release()
        amb = null; ambFile = null
        entity?.dispose(); entity = null
        onPlayInfo("")
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
