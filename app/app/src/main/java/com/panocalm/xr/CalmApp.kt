package com.panocalm.xr

import android.app.Application
import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.provider.MediaStore
import java.io.File

/** Saves any crash's stack trace so it can be shown on the next start and read from the headset's Download folder
 *  (Download/Calm360_crash_<time>.txt) without adb. */
class CalmApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val prev = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { t, e ->
            try {
                val text = "Calm 360 ${BuildConfigLite.version(this)} / Android ${Build.VERSION.RELEASE} (${Build.MODEL})\n" +
                    "thread: ${t.name}\n" + e.stackTraceToString()
                crashFile(this).writeText(text)
                val cv = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, "Calm360_crash_${System.currentTimeMillis() / 1000}.txt")
                    put(MediaStore.MediaColumns.MIME_TYPE, "text/plain")
                }
                contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, cv)?.let { u ->
                    contentResolver.openOutputStream(u)?.use { it.write(text.toByteArray()) }
                }
            } catch (_: Throwable) { }
            prev?.uncaughtException(t, e)
        }
    }

    companion object {
        fun crashFile(ctx: Context) = File(ctx.filesDir, "last_crash.txt")
    }
}

object BuildConfigLite {
    fun version(ctx: Context): String = try {
        ctx.packageManager.getPackageInfo(ctx.packageName, 0).versionName ?: "?"
    } catch (_: Throwable) { "?" }
}
