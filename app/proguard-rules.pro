# 保留 WebView JS 桥接相关（当前未使用，预留）
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# androidx.webkit 自带 consumer rules，无需额外配置
-dontwarn org.chromium.**
