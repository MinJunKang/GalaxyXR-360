package com.panocalm.xr

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import java.io.File

/** 512x256 card thumbnails, made once from the photo/video itself and cached in the app cache folder. */
object Thumbs {
    fun load(ctx: Context, item: Item): Bitmap? = try {
        item.thumb?.let { u -> ctx.contentResolver.openInputStream(u)?.use { BitmapFactory.decodeStream(it) } }
            ?: run {
                val dir = File(ctx.cacheDir, "thumbs").apply { mkdirs() }
                val f = File(dir, Integer.toHexString((item.uri.toString() + item.width).hashCode()) + ".jpg")
                if (f.exists()) return BitmapFactory.decodeFile(f.absolutePath)
                val bmp = if (item.kind == Item.Kind.PHOTO) {
                    val o = BitmapFactory.Options().apply { inSampleSize = maxOf(1, Integer.highestOneBit(item.width / 512)) }
                    ctx.contentResolver.openInputStream(item.uri)?.use { BitmapFactory.decodeStream(it, null, o) }
                } else MediaMetadataRetriever().use { r ->
                    r.setDataSource(ctx, item.uri)
                    r.getScaledFrameAtTime(1_000_000, MediaMetadataRetriever.OPTION_CLOSEST_SYNC, 512, 256)
                }
                bmp?.let { b ->
                    val s = Bitmap.createScaledBitmap(b, 512, 256, true)
                    f.outputStream().use { s.compress(Bitmap.CompressFormat.JPEG, 85, it) }
                    s
                }
            }
    } catch (e: Exception) { null }
}
