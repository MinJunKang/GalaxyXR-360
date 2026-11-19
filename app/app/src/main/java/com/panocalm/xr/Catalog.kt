package com.panocalm.xr

import android.content.ContentUris
import android.content.Context
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.provider.DocumentsContract
import android.provider.MediaStore
import org.json.JSONObject
import java.io.File

/** One playable 360 item (equirectangular photo or video). [uri] is file:// (adb folder) or content:// (downloads, picked folders). */
data class Item(
    val key: String,
    val themeId: String,
    val title: String,
    val category: String,
    val kind: Kind,
    val uri: Uri,
    val name: String,
    /** pre-made thumbnail (adb manifest); otherwise one is generated from the file and cached */
    val thumb: Uri?,
    val width: Int,
    val height: Int,
    /** looping ambience for photos (stereo .m4a with the same file name); videos carry their sound inside the mp4 */
    val audio: Uri? = null,
) {
    enum class Kind { PHOTO, VIDEO }
}

data class Category(val id: String, val label: String)

/**
 * Where the app looks for 360 content (all merged, duplicates by file name dropped):
 *  1. Files downloaded on the headset (Chrome / Google Drive -> Download, or any other folder): found through MediaStore
 *     once "사진 및 동영상" and "음악 및 오디오" access is allowed. Only 2:1 equirectangular images/videos are listed.
 *  2. Folders the user picked with "📂 폴더 추가" (Storage Access Framework, permission kept across restarts).
 *  3. The adb folder /sdcard/Android/media/com.panocalm.xr/content/ with manifest.json (older install method).
 * A photo's sound is the audio file with the same base name in the same place (forest_morning_p1.jpg + forest_morning_p1.m4a).
 */
object Catalog {
    val categories = listOf(
        Category("all", "전체"), Category("healing", "힐링"), Category("ocean", "바다"), Category("underwater", "바다 속"),
        Category("space", "우주"), Category("scifi", "SF"), Category("desert", "사막"), Category("countryside", "시골"),
        Category("jurassic", "쥐라기"), Category("medieval", "중세"), Category("fantasy", "판타지"), Category("city", "도시"),
        Category("etc", "기타"),
    )
    private val IMG = setOf("jpg", "jpeg", "png", "webp")
    private val VID = setOf("mp4", "mkv", "webm", "mov")
    private val AUD = setOf("m4a", "aac", "mp3", "wav", "ogg", "flac", "opus")

    fun contentDir(ctx: Context): File {
        val base = ctx.externalMediaDirs.firstOrNull { it != null } ?: ctx.getExternalFilesDir(null)!!
        return File(base, "content")
    }

    private class Found(val name: String, val uri: Uri, val group: String, var w: Int, var h: Int)

    private var themes: Map<String, Pair<String, String>>? = null
    private fun themes(ctx: Context): Map<String, Pair<String, String>> = themes ?: run {
        val o = JSONObject(ctx.assets.open("themes.json").bufferedReader().readText())
        o.keys().asSequence().associateWith { k -> o.getJSONObject(k).let { it.getString("ko") to it.getString("category") } }
            .also { themes = it }
    }

    fun load(ctx: Context): Pair<List<Item>, String?> {
        val out = LinkedHashMap<String, Item>()
        val notes = ArrayList<String>()
        try { loadManifest(ctx, out) } catch (e: Exception) { notes += "adb 폴더의 manifest.json 을 읽지 못했습니다: ${e.message}" }
        val media = ArrayList<Found>(); val audio = ArrayList<Found>()
        try { scanMediaStore(ctx, media, audio) } catch (e: SecurityException) { /* no media permission yet */ } catch (e: Exception) { notes += "다운로드 파일 검색 오류: ${e.message}" }
        for (p in ctx.contentResolver.persistedUriPermissions) {
            if (!p.isReadPermission) continue
            try { scanTree(ctx, p.uri, media, audio) } catch (e: Exception) { notes += "선택한 폴더를 읽지 못했습니다: ${e.message}" }
        }
        val audioByBase = HashMap<String, Uri>()
        for (a in audio) { audioByBase.putIfAbsent(a.group + "|" + base(a.name), a.uri); audioByBase.putIfAbsent("*|" + base(a.name), a.uri) }
        for (f in media.sortedBy { it.name.lowercase() }) {
            val key = f.name.lowercase()
            if (key in out) continue
            val kind = if (ext(f.name) in VID) Item.Kind.VIDEO else Item.Kind.PHOTO
            if (f.w <= 0 || f.h <= 0) fillSize(ctx, f, kind)
            if (f.h <= 0 || kotlin.math.abs(f.w - 2 * f.h) > f.h / 50 || f.w < 2048) continue   // equirectangular 2:1 only
            val (themeId, title, cat) = describe(ctx, f.name)
            val b = base(f.name)
            out[key] = Item(key, themeId, title, cat, kind, f.uri, f.name, null, f.w, f.h,
                audio = if (kind == Item.Kind.PHOTO) (audioByBase[f.group + "|" + b] ?: audioByBase["*|" + b]) else null)
        }
        val items = out.values.sortedWith(compareBy({ categories.indexOfFirst { c -> c.id == it.category } }, { it.themeId }, { it.kind }, { it.name }))
        val msg = when {
            items.isEmpty() -> "아직 360° 사진·영상이 없습니다.\n" +
                "• Google Drive 에서 사진(.jpg)·소리(.m4a)·영상(.mp4)을 헤드셋으로 다운로드한 뒤 🔄 새로고침을 누르세요 (사진 및 동영상·음악 및 오디오 접근 허용 필요).\n" +
                "• 다른 폴더에 있으면 📂 폴더 추가로 그 폴더를 선택하세요."
            else -> null
        }
        return items to (listOfNotNull(msg) + notes).joinToString("\n").ifEmpty { null }
    }

    private fun loadManifest(ctx: Context, out: MutableMap<String, Item>) {
        val dir = contentDir(ctx)
        val mf = File(dir, "manifest.json")
        if (!mf.exists()) return
        val themesArr = JSONObject(mf.readText()).getJSONArray("themes")
        for (i in 0 until themesArr.length()) {
            val t = themesArr.getJSONObject(i)
            for ((k, kind) in listOf("photos" to Item.Kind.PHOTO, "videos" to Item.Kind.VIDEO)) {
                val arr = t.optJSONArray(k) ?: continue
                for (j in 0 until arr.length()) {
                    val e = arr.getJSONObject(j)
                    val f = File(dir, e.getString("file"))
                    if (!f.exists()) continue
                    val key = f.name.lowercase()
                    out[key] = Item(key, t.getString("id"), t.getString("ko") + " " + (j + 1), t.getString("category"), kind,
                        Uri.fromFile(f), f.name, File(dir, e.getString("thumb")).takeIf { it.exists() }?.let { Uri.fromFile(it) },
                        e.getInt("width"), e.getInt("height"),
                        audio = e.optString("audio", "").takeIf { it.isNotEmpty() }?.let { File(dir, it) }?.takeIf { it.exists() }?.let { Uri.fromFile(it) })
                }
            }
        }
    }

    private fun scanMediaStore(ctx: Context, media: MutableList<Found>, audio: MutableList<Found>) {
        val cr = ctx.contentResolver
        val vol = MediaStore.VOLUME_EXTERNAL
        for (coll in listOf(MediaStore.Images.Media.getContentUri(vol), MediaStore.Video.Media.getContentUri(vol))) {
            cr.query(coll, arrayOf(MediaStore.MediaColumns._ID, MediaStore.MediaColumns.DISPLAY_NAME, MediaStore.MediaColumns.WIDTH,
                MediaStore.MediaColumns.HEIGHT, MediaStore.MediaColumns.RELATIVE_PATH), null, null, null)?.use { c ->
                while (c.moveToNext()) {
                    val name = c.getString(1) ?: continue
                    if (ext(name) !in IMG && ext(name) !in VID) continue
                    media += Found(name, ContentUris.withAppendedId(coll, c.getLong(0)), c.getString(4) ?: "", c.getInt(2), c.getInt(3))
                }
            }
        }
        val ac = MediaStore.Audio.Media.getContentUri(vol)
        cr.query(ac, arrayOf(MediaStore.MediaColumns._ID, MediaStore.MediaColumns.DISPLAY_NAME, MediaStore.MediaColumns.RELATIVE_PATH), null, null, null)?.use { c ->
            while (c.moveToNext()) {
                val name = c.getString(1) ?: continue
                if (ext(name) in AUD) audio += Found(name, ContentUris.withAppendedId(ac, c.getLong(0)), c.getString(2) ?: "", 0, 0)
            }
        }
    }

    /** recursive walk of a folder picked with ACTION_OPEN_DOCUMENT_TREE */
    private fun scanTree(ctx: Context, tree: Uri, media: MutableList<Found>, audio: MutableList<Found>) {
        val stack = ArrayDeque<String>().apply { add(DocumentsContract.getTreeDocumentId(tree)) }
        var guard = 0
        while (stack.isNotEmpty() && guard++ < 2000) {
            val docId = stack.removeLast()
            val children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, docId)
            ctx.contentResolver.query(children, arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID, DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                DocumentsContract.Document.COLUMN_MIME_TYPE), null, null, null)?.use { c ->
                while (c.moveToNext()) {
                    val id = c.getString(0); val name = c.getString(1) ?: continue
                    if (c.getString(2) == DocumentsContract.Document.MIME_TYPE_DIR) { stack.add(id); continue }
                    val uri = DocumentsContract.buildDocumentUriUsingTree(tree, id)
                    when (ext(name)) {
                        in IMG, in VID -> media += Found(name, uri, "tree:$docId", 0, 0)
                        in AUD -> audio += Found(name, uri, "tree:$docId", 0, 0)
                    }
                }
            }
        }
    }

    private fun fillSize(ctx: Context, f: Found, kind: Item.Kind) {
        try {
            if (kind == Item.Kind.PHOTO) {
                val o = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                ctx.contentResolver.openInputStream(f.uri)?.use { BitmapFactory.decodeStream(it, null, o) }
                f.w = o.outWidth; f.h = o.outHeight
            } else {
                MediaMetadataRetriever().use { r ->
                    r.setDataSource(ctx, f.uri)
                    f.w = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)?.toIntOrNull() ?: 0
                    f.h = r.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)?.toIntOrNull() ?: 0
                }
            }
        } catch (e: Exception) { f.w = 0; f.h = 0 }
    }

    /** "forest_morning_p1_8k.jpg" -> theme forest_morning, "아침 숲 사진 1"; unknown names keep the file name under 기타 */
    private fun describe(ctx: Context, name: String): Triple<String, String, String> {
        val b = base(name)
        val th = themes(ctx)
        val id = th.keys.filter { b == it || b.startsWith(it + "_") }.maxByOrNull { it.length }
            ?: return Triple("zz_" + b, b, "etc")
        val (ko, cat) = th.getValue(id)
        val m = Regex("_([pv])(\\d+)").find(b.removePrefix(id))
        val title = when {
            m == null -> ko
            m.groupValues[1] == "p" -> "$ko 사진 ${m.groupValues[2]}"
            else -> "$ko 영상 ${m.groupValues[2]}"
        }
        return Triple(id, title, cat)
    }

    private fun ext(n: String) = n.substringAfterLast('.', "").lowercase()
    /** base name used to pair a photo with its sound; tolerates "(1)" copies made by repeated downloads */
    private fun base(n: String) = n.substringBeforeLast('.').lowercase().replace(Regex("\\s*\\(\\d+\\)$"), "")
}
