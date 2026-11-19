package com.panocalm.xr

import android.graphics.BitmapFactory
import android.os.Bundle
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
import androidx.xr.scenecore.scene
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class MainActivity : ComponentActivity() {
    private var session: Session? = null
    private var viewer: SphereViewer? = null
    private var gridPanelSize: FloatSize2d? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val (items, msg) = Catalog.load(this)
        var status by mutableStateOf(msg)
        lifecycleScope.launch {
            when (val r = Session.create(this@MainActivity)) {
                is SessionCreateSuccess -> {
                    session = r.session
                    viewer = SphereViewer(this@MainActivity, r.session, lifecycleScope).also { v -> v.onError = { status = it } }
                }
                else -> status = "Android XR 세션을 만들 수 없습니다 (${r::class.simpleName}). Galaxy XR 에서 실행해 주세요."
            }
        }
        setContent {
            MaterialTheme(colorScheme = darkColorScheme(primary = Color(0xFF8FD3C7))) {
                Surface(Modifier.fillMaxSize(), color = Color(0xFF101418)) {
                    App(items, status, ::open, ::close, { viewer?.togglePause() })
                }
            }
        }
    }

    private fun open(item: Item) {
        val v = viewer ?: return
        val s = session ?: return
        if (gridPanelSize == null) gridPanelSize = s.scene.mainPanelEntity.size
        v.enterImmersive()
        v.show(item)
        s.scene.mainPanelEntity.size = FloatSize2d(0.9f, 0.16f)      // compact control bar while immersed
    }

    private fun close() {
        viewer?.exitImmersive()
        val s = session ?: return
        gridPanelSize?.let { s.scene.mainPanelEntity.size = it }
    }

    override fun onDestroy() {
        viewer?.close()
        super.onDestroy()
    }
}

/** 한 편 반복: the current 360 video/photo loops forever. 전체 반복: each item stays for `dwellSec`, then the next one, wrapping around. */
enum class RepeatMode { ONE, ALL }

@Composable
private fun App(items: List<Item>, status: String?, open: (Item) -> Unit, close: () -> Unit, pause: () -> Unit) {
    var cat by remember { mutableStateOf("all") }
    var kind by remember { mutableStateOf<Item.Kind?>(null) }
    var current by remember { mutableStateOf<Int?>(null) }
    var mode by remember { mutableStateOf(RepeatMode.ONE) }
    var dwellSec by remember { mutableStateOf(60) }
    var paused by remember { mutableStateOf(false) }
    val shown = items.filter { (cat == "all" || it.category == cat) && (kind == null || it.kind == kind) }

    val idx = current
    // 전체 반복: advance after dwellSec unless paused; restarts whenever the item, mode, dwell or pause state changes
    LaunchedEffect(idx, mode, dwellSec, paused) {
        if (idx != null && mode == RepeatMode.ALL && !paused && shown.isNotEmpty()) {
            kotlinx.coroutines.delay(dwellSec * 1000L)
            val n = (idx + 1) % shown.size; current = n; open(shown[n])
        }
    }
    if (idx != null && idx in shown.indices) {
        BackHandler { current = null; paused = false; close() }
        ControlBar(shown[idx], idx, shown.size, mode, dwellSec, paused,
            onPrev = { val n = (idx - 1 + shown.size) % shown.size; current = n; open(shown[n]) },
            onNext = { val n = (idx + 1) % shown.size; current = n; open(shown[n]) },
            onPause = { paused = !paused; pause() },
            onMode = { mode = if (mode == RepeatMode.ONE) RepeatMode.ALL else RepeatMode.ONE },
            onDwell = { dwellSec = when (dwellSec) { 30 -> 60; 60 -> 180; 180 -> 300; else -> 30 } },
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
        status?.let { Text(it, color = Color(0xFFFFCC80), modifier = Modifier.padding(vertical = 8.dp)) }
        Spacer(Modifier.height(8.dp))
        LazyVerticalGrid(GridCells.Adaptive(260.dp), horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)) {
            items(shown, key = { it.file.name }) { it2 ->
                Card(it2) { mode = RepeatMode.ONE; paused = false; current = shown.indexOf(it2); open(it2) }
            }
        }
    }
}

@Composable
private fun Card(item: Item, onClick: () -> Unit) {
    val img by produceState<ImageBitmap?>(null, item.thumb) {
        value = withContext(Dispatchers.IO) { loadThumb(item.thumb) }
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
private fun ControlBar(item: Item, idx: Int, total: Int, mode: RepeatMode, dwellSec: Int, paused: Boolean,
                       onPrev: () -> Unit, onNext: () -> Unit, onPause: () -> Unit, onMode: () -> Unit, onDwell: () -> Unit, onBack: () -> Unit) {
    Row(Modifier.fillMaxSize().padding(horizontal = 20.dp), verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        OutlinedButton(onBack) { Text("✕ 목록") }
        Column(Modifier.weight(1f)) {
            Text(item.title, color = Color.White, fontSize = 18.sp)
            Text("${idx + 1} / $total", color = Color(0xFFB0BEC5), fontSize = 13.sp)
        }
        Button(onPrev) { Text("◀ 이전") }
        Button(onPause) { Text(if (paused) "▶ 재생" else "⏸ 일시정지") }
        Button(onNext) { Text("다음 ▶") }
        FilterChip(mode == RepeatMode.ALL, onMode, { Text(if (mode == RepeatMode.ONE) "🔂 한 편 반복" else "🔁 전체 반복") })
        if (mode == RepeatMode.ALL) OutlinedButton(onDwell) { Text(if (dwellSec < 60) "${dwellSec}초씩" else "${dwellSec / 60}분씩") }
    }
}

private fun loadThumb(f: File): ImageBitmap? =
    if (f.exists()) BitmapFactory.decodeFile(f.absolutePath)?.asImageBitmap() else null
