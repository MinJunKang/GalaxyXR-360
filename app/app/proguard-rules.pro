# keep Jetpack XR / SceneCore / runtime (loaded via reflection and JNI)
-keep class androidx.xr.** { *; }
-keep class com.android.extensions.xr.** { *; }
-dontwarn com.android.extensions.xr.**
-dontwarn androidx.xr.**
-keep class com.google.androidxr.** { *; }
-dontwarn com.google.**
