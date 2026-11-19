package com.panocalm.xr

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.ui.platform.LocalContext
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.border
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.lifecycleScope
import androidx.xr.runtime.Session
import androidx.xr.runtime.SessionCreateSuccess
import androidx.xr.runtime.math.FloatSize2d
import androidx.xr.runtime.math.Pose
import androidx.xr.runtime.math.Quaternion
import androidx.xr.runtime.math.Vector3
import androidx.xr.scenecore.scene
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    private var session: Session? = null
    private var viewer: SphereViewer? = null
    private var gridPanelSize: FloatSize2d? = null
    private var gridPanelPose: Pose? = null
    var panelHidden by mutableStateOf(false); private set
    private var playInfo by mutableStateOf("")

    private var items by mutableStateOf<List<Item>>(emptyList())
    private var status by mutableStateOf<String?>("불러오는 중…")
    private var scanning by mutableStateOf(false)
    private var lastCrash by mutableStateOf<String?>(null)

    private val MEDIA_PERMS = arrayOf(Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO, Manifest.permission.READ_MEDIA_AUDIO)
    private val askMedia = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { refresh() }
    private val pickFolder = registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        if (uri != null) {
            try { contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION) } catch (e: SecurityException) { }
            refresh()
        }
    }

    /** rescan downloads, picked folders and the adb folder (also when coming back from the browser / Files app) */
    fun refresh() {
        if (scanning) return
        scanning = true
        lifecycleScope.launch {
            val (list, msg) = withContext(Dispatchers.IO) { Catalog.load(this@MainActivity) }
            items = list
            val noPerm = MEDIA_PERMS.any { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
            status = listOfNotNull(lastCrash?.let { "⚠ 지난번 실행이 오류로 멈췄습니다 (Download 폴더의 Calm360_crash_*.txt 에 저장됨):\n$it" }, msg, if (noPerm) "다운로드한 파일을 자동으로 찾으려면 🔓 파일 접근 허용을 눌러 주세요." else null).joinToString("\n").ifEmpty { null }
            scanning = false
        }
    }

    override fun onResume() {
        super.onResume()
        if (viewer?.isShowing != true) refresh() else if (panelHidden && System.currentTimeMillis() - hiddenAt > 2000) showPanel()   // back from the system menu: show the bar again
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val crash = CalmApp.crashFile(this)
        if (crash.exists()) {
            lastCrash = crash.readText().lines().take(14).joinToString("\n")
            crash.delete()
        }
        if (MEDIA_PERMS.any { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }) askMedia.launch(MEDIA_PERMS)
        lifecycleScope.launch {
            val r = try { Session.create(this@MainActivity) } catch (t: Throwable) {
                status = "Android XR 세션 오류: ${t::class.simpleName}: ${t.message}"; return@launch
            }
            when (r) {
                is SessionCreateSuccess -> {
                    session = r.session
                    viewer = SphereViewer(this@MainActivity, r.session, lifecycleScope).also { v -> v.onError = { status = it }; v.onTap = { showPanel() }; v.onPlayInfo = { playInfo = it } }
                }
                else -> status = "Android XR 세션을 만들 수 없습니다 (${r::class.simpleName}). Galaxy XR 에서 실행해 주세요."
            }
        }
        setContent {
            MaterialTheme(colorScheme = darkColorScheme(primary = Color(0xFF8FD3C7))) {
                Surface(Modifier.fillMaxSize(), color = Color(0xFF101418)) {
                    App(items, status, scanning, ::open, ::close, { viewer?.togglePause() }, { dx, dy -> viewer?.rotateBy(dx, dy) }, { viewer?.resetView() },
                        onTurn = { viewer?.turn(it) }, onLevel = { viewer?.levelNow() }, onKeepLevel = { viewer?.keepLevel = it },
                        onHide = ::hidePanel, panelHidden = panelHidden, playInfo = playInfo, onShowPanel = ::showPanel,
                        onRefresh = ::refresh, onAddFolder = { pickFolder.launch(null) }, onAskPerm = { askMedia.launch(MEDIA_PERMS) })
                }
            }
        }
    }

    private fun open(item: Item) {
        val v = viewer ?: return
        val s = session ?: return
        val panel = s.scene.mainPanelEntity
        if (gridPanelSize == null) { gridPanelSize = panel.size; gridPanelPose = panel.getPose() }
        v.enterImmersive()
        v.show(item)
        panel.size = FloatSize2d(1.25f, 0.26f)      // compact control bar + look-around pad while immersed
        // move the bar below the line of sight and tilt it up toward the viewer, so the 360 scene ahead stays clear
        gridPanelPose?.let { g ->
            panel.setPose(Pose(g.translation + Vector3(0f, -0.55f, 0.15f), g.rotation * Quaternion.fromAxisAngle(Vector3.Right, -30f)))
        }
        hidePanel()                                  // menu hidden by default; pinch the 360 scene once to bring it back
    }

    private var hiddenAt = 0L
    fun hidePanel() { session?.scene?.mainPanelEntity?.setEnabled(false); panelHidden = true; hiddenAt = System.currentTimeMillis() }
    fun showPanel() { session?.scene?.mainPanelEntity?.setEnabled(true); panelHidden = false }

    private fun close() {
        viewer?.exitImmersive()
        val s = session ?: return
        showPanel()
        gridPanelSize?.let { s.scene.mainPanelEntity.size = it }
        gridPanelPose?.let { s.scene.mainPanelEntity.setPose(it) }
    }

    override fun onDestroy() {
        viewer?.close()
        super.onDestroy()
    }
}

/** 한 편 반복: the current 360 video/photo loops forever. 전체 반복: each item stays for `dwellSec`, then the next one, wrapping around. */
enum class RepeatMode { ONE, ALL }

@Composable
private fun App(items: List<Item>, status: String?, scanning: Boolean, open: (Item) -> Unit, close: () -> Unit, pause: () -> Unit,
                rotate: (Float, Float) -> Unit, resetView: () -> Unit,
                onTurn: (Float) -> Unit, onLevel: () -> Unit, onKeepLevel: (Boolean) -> Unit,
                onHide: () -> Unit, panelHidden: Boolean, playInfo: String, onShowPanel: () -> Unit,
                onRefresh: () -> Unit, onAddFolder: () -> Unit, onAskPerm: () -> Unit) {
    var cat by remember { mutableStateOf("all") }
    var kind by remember { mutableStateOf<Item.Kind?>(null) }
    var current by remember { mutableStateOf<Int?>(null) }
    var mode by remember { mutableStateOf(RepeatMode.ONE) }
    var dwellSec by remember { mutableStateOf(60) }
    var paused by remember { mutableStateOf(false) }
    val shown = items.filter { (cat == "all" || it.category == cat) && (kind == null || it.kind == kind) }

    val idx = current
    // 전체 반복: count down dwellSec (shown on the bar), then the next item, wrapping around; restarts on item/mode/dwell/pause change
    var remain by remember { mutableStateOf(0) }
    LaunchedEffect(idx, mode, dwellSec, paused) {
        remain = dwellSec
        if (idx != null && mode == RepeatMode.ALL && !paused && shown.isNotEmpty()) {
            while (remain > 0) { kotlinx.coroutines.delay(1000L); remain -= 1 }
            val n = (idx + 1) % shown.size
            current = n; open(shown[n])
            if (n == idx) remain = dwellSec             // a single item: just keep it on
        }
    }
    if (idx != null && idx in shown.indices) {
        BackHandler { if (panelHidden) onShowPanel() else { current = null; paused = false; close() } }
        ControlBar(shown[idx], idx, shown.size, mode, dwellSec, paused, remain, playInfo, onHide,
            onPrev = { val n = (idx - 1 + shown.size) % shown.size; current = n; open(shown[n]) },
            onNext = { val n = (idx + 1) % shown.size; current = n; open(shown[n]) },
            onPause = { paused = !paused; pause() },
            onMode = { mode = if (mode == RepeatMode.ONE) RepeatMode.ALL else RepeatMode.ONE },
            onDwell = { dwellSec = when (dwellSec) { 30 -> 60; 60 -> 180; 180 -> 300; else -> 30 } },
            rotate = rotate, resetView = resetView, onTurn = onTurn, onLevel = onLevel, onKeepLevel = onKeepLevel,
            onBack = { current = null; paused = false; close() })
        return
    }
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Calm 360", fontSize = 30.sp, fontWeight = FontWeight.Bold, color = Color.White)
                Text("마음이 편안해지는 360° 공간 · 사진 ${items.count { it.kind == Item.Kind.PHOTO }} · 영상 ${items.count { it.kind == Item.Kind.VIDEO }}",
                    color = Color(0xFFB0BEC5), fontSize = 15.sp)
            }
            Button(onClick = { if (shown.isNotEmpty()) { mode = RepeatMode.ALL; paused = false; current = 0; open(shown[0]) } },
                enabled = shown.isNotEmpty()) { Text("▶ 전체 연속 재생 (${shown.size})") }
        }
        Spacer(Modifier.height(12.dp))
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(kind == null, { kind = null }, { Text("사진+영상") })
            FilterChip(kind == Item.Kind.VIDEO, { kind = Item.Kind.VIDEO }, { Text("영상") })
            FilterChip(kind == Item.Kind.PHOTO, { kind = Item.Kind.PHOTO }, { Text("사진") })
            Spacer(Modifier.width(16.dp))
            for (c in Catalog.categories) FilterChip(cat == c.id, { cat = c.id }, { Text(c.label) })
        }
        Row(Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
            OutlinedButton(onRefresh, enabled = !scanning) { Text(if (scanning) "찾는 중…" else "🔄 새로고침") }
            OutlinedButton(onAddFolder) { Text("📂 폴더 추가") }
            OutlinedButton(onAskPerm) { Text("🔓 파일 접근 허용") }
            Text("${items.size}개 · 사진 ${items.count { it.kind == Item.Kind.PHOTO }} · 영상 ${items.count { it.kind == Item.Kind.VIDEO }}",
                color = Color(0xFFB0BEC5), fontSize = 13.sp)
        }
        status?.let { Text(it, color = Color(0xFFFFCC80), modifier = Modifier.padding(vertical = 8.dp)) }
        Spacer(Modifier.height(8.dp))
        LazyVerticalGrid(GridCells.Adaptive(260.dp), horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)) {
            items(shown, key = { it.key }) { it2 ->
                Card(it2) { mode = RepeatMode.ONE; paused = false; current = shown.indexOf(it2); open(it2) }
            }
        }
    }
}

@Composable
private fun Card(item: Item, onClick: () -> Unit) {
    val ctx = LocalContext.current
    val img by produceState<ImageBitmap?>(null, item.key) {
        value = withContext(Dispatchers.IO) { Thumbs.load(ctx, item)?.asImageBitmap() }
    }
    Column(Modifier.clip(RoundedCornerShape(14.dp)).background(Color(0xFF1C2329)).clickable(onClick = onClick)) {
        Box(Modifier.fillMaxWidth().aspectRatio(2f).background(Color(0xFF263238))) {
            img?.let { Image(it, item.title, Modifier.fillMaxSize(), contentScale = ContentScale.Crop) }
            Text(if (item.kind == Item.Kind.VIDEO) "▶ 영상" else "◉ 사진", color = Color.White, fontSize = 12.sp,
                modifier = Modifier.padding(8.dp).clip(RoundedCornerShape(6.dp)).background(Color(0x99000000)).padding(horizontal = 8.dp, vertical = 3.dp))
        }
        Text(item.title, color = Color.White, fontSize = 16.sp, modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp))
    }
}

@Composable
private fun ControlBar(item: Item, idx: Int, total: Int, mode: RepeatMode, dwellSec: Int, paused: Boolean, remain: Int, playInfo: String, onHide: () -> Unit,
                       onPrev: () -> Unit, onNext: () -> Unit, onPause: () -> Unit, onMode: () -> Unit, onDwell: () -> Unit,
                       rotate: (Float, Float) -> Unit, resetView: () -> Unit, onTurn: (Float) -> Unit, onLevel: () -> Unit,
                       onKeepLevel: (Boolean) -> Unit, onBack: () -> Unit) {
    var level by remember { mutableStateOf(true) }
    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp, vertical = 10.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedButton(onBack) { Text("✕ 목록") }
            OutlinedButton(onHide) { Text("👁 창 숨기기") }
            Column(Modifier.weight(1f)) {
                Text(item.title, color = Color.White, fontSize = 18.sp)
                Text("${idx + 1} / $total · " + when {
                    mode == RepeatMode.ONE -> "🔂 이 장면을 계속 반복"
                    paused -> "⏸ 일시정지"
                    else -> "🔁 다음 장면까지 ${remain}초"
                } + (if (playInfo.isNotEmpty()) " · $playInfo" else ""), color = Color(0xFFB0BEC5), fontSize = 13.sp)
            }
            Button(onPrev) { Text("◀ 이전") }
            Button(onPause) { Text(if (paused) "▶ 재생" else "⏸ 일시정지") }
            Button(onNext) { Text("다음 ▶") }
            FilterChip(mode == RepeatMode.ALL, onMode, { Text(if (mode == RepeatMode.ONE) "🔂 한 편 반복" else "🔁 전체 반복") })
            if (mode == RepeatMode.ALL) OutlinedButton(onDwell) { Text(if (dwellSec < 60) "${dwellSec}초씩" else "${dwellSec / 60}분씩") }
        }
        // look-around: pinch-drag on this pad (or directly on the 360 scene) to turn the view; buttons turn in 30 degree steps
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedButton({ onTurn(-30f) }) { Text("↺ 30°") }
            Box(Modifier.weight(1f).height(56.dp).clip(RoundedCornerShape(12.dp)).background(Color(0xFF1C2329))
                .border(1.dp, Color(0xFF37474F), RoundedCornerShape(12.dp))
                .pointerInput(Unit) { detectDragGestures { change, drag -> change.consume(); rotate(-drag.x * 0.25f, -drag.y * 0.25f) } },
                contentAlignment = Alignment.Center) {
                Text("✋ 집어서 어느 방향으로든 끌면 장면이 돕니다 · 창을 숨긴 뒤에는 360° 화면을 한 번 집으면 창이 다시 나타납니다", color = Color(0xFFB0BEC5), fontSize = 14.sp)
            }
            OutlinedButton({ onTurn(30f) }) { Text("30° ↻") }
            OutlinedButton(resetView) { Text("⌂ 정면") }
            OutlinedButton(onLevel) { Text("⇔ 수평 맞추기") }
            FilterChip(level, { level = !level; onKeepLevel(level) }, { Text("🧭 수평 유지") })
        }
    }
}

