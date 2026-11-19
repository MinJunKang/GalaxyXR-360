package com.panocalm.xr

import android.content.Context
import org.json.JSONObject
import java.io.File

/** One playable 360 item (equirectangular photo or video) in the content folder. */
data class Item(
    val themeId: String,
    val title: String,
    val category: String,
    val kind: Kind,
    val file: File,
    val thumb: File,
    val width: Int,
    val height: Int,
    /** looping ambience for photos (stereo .m4a); videos carry their sound inside the mp4 */
    val audio: File? = null,
) {
    enum class Kind { PHOTO, VIDEO }
}

data class Category(val id: String, val label: String)

/**
 * Content lives outside the APK (≈20 GB) in the app's media folder, pushed with adb:
 *   /sdcard/Android/media/com.panocalm.xr/content/{manifest.json, photos/, videos/, thumbs/}
 */
object Catalog {
    val categories = listOf(
        Category("all", "전체"), Category("healing", "힐링"), Category("ocean", "바다"), Category("underwater", "바다 속"),
        Category("space", "우주"), Category("scifi", "SF"), Category("desert", "사막"), Category("countryside", "시골"),
        Category("jurassic", "쥐라기"), Category("medieval", "중세"), Category("fantasy", "판타지"), Category("city", "도시"),
    )

    fun contentDir(ctx: Context): File {
        val base = ctx.externalMediaDirs.firstOrNull { it != null } ?: ctx.getExternalFilesDir(null)!!
        return File(base, "content")
    }

    fun load(ctx: Context): Pair<List<Item>, String?> {
        val dir = contentDir(ctx)
        val mf = File(dir, "manifest.json")
        if (!mf.exists()) return emptyList<Item>() to "콘텐츠가 없습니다.\nadb push 로 ${dir.absolutePath} 에 content 폴더를 넣어 주세요."
        return try {
            val root = JSONObject(mf.readText())
            val themes = root.getJSONArray("themes")
            val out = ArrayList<Item>()
            for (i in 0 until themes.length()) {
                val t = themes.getJSONObject(i)
                for ((key, kind) in listOf("photos" to Item.Kind.PHOTO, "videos" to Item.Kind.VIDEO)) {
                    val arr = t.optJSONArray(key) ?: continue
                    for (j in 0 until arr.length()) {
                        val e = arr.getJSONObject(j)
                        val f = File(dir, e.getString("file"))
                        if (!f.exists()) continue
                        out += Item(
                            themeId = t.getString("id"), title = t.getString("ko") + " " + (j + 1),
                            category = t.getString("category"), kind = kind, file = f,
                            thumb = File(dir, e.getString("thumb")), width = e.getInt("width"), height = e.getInt("height"),
                            audio = e.optString("audio", "").takeIf { it.isNotEmpty() }?.let { File(dir, it) }?.takeIf { it.exists() },
                        )
                    }
                }
            }
            out to (if (out.isEmpty()) "manifest.json 은 있지만 재생 가능한 파일이 없습니다." else null)
        } catch (e: Exception) {
            emptyList<Item>() to "manifest.json 을 읽지 못했습니다: ${e.message}"
        }
    }
}
