package com.membo.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ContentValues;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.text.InputType;
import android.util.Base64;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowInsets;
import android.view.animation.DecelerateInterpolator;
import android.webkit.JavascriptInterface;
import android.webkit.JsPromptResult;
import android.webkit.JsResult;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.OutputStream;

import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewClientCompat;

public class MainActivity extends Activity {

    // 启动图标尺寸
    private static final int ICON_DP = 116;
    // 图标放大倍数：从居中一点撑开
    private static final float ICON_SCALE = 1.9f;
    // 图标放大并消失的时长
    private static final long ICON_MS = 420L;
    // 页面淡入时长，严格在图标消失之后开始
    private static final long PAGE_MS = 460L;
    // 页面迟迟没渲染完也不能一直卡在启动图
    private static final long REVEAL_TIMEOUT_MS = 1600L;
    // 首页 #viewHome 是纯白，启动底色必须一致，否则放大时会闪一下
    private static final int WINDOW_BG = 0xFFFFFFFF;

    private WebView webView;
    private ImageView splashIcon;
    private boolean revealed;
    private float pageOffsetPx;
    private int lastTopInset = -1;
    private int lastBottomInset = -1;

    // 页面里的 <input type="file"> 需要原生回传，否则点上传毫无反应
    private static final int REQ_FILE_CHOOSER = 1001;
    private ValueCallback<Uri[]> filePathCallback;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable revealTask = new Runnable() {
        @Override
        public void run() {
            reveal();
        }
    };

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 上次如果崩过，先把堆栈显示出来，方便定位
        showLastCrashIfAny();

        // 真 edge-to-edge：状态栏导航栏全透明，内容铺到屏幕边缘，
        // 让页面自己的安全区变量去避让，学习页顶部就不会再有一条白带。
        // 任何异常都降级成不透明系统栏，绝不让启动挂掉
        try {
            setupEdgeToEdge();
        } catch (Throwable t) {
            fallbackOpaqueBars();
        }

        pageOffsetPx = 6 * getResources().getDisplayMetrics().density;

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(WINDOW_BG);

        // 系统栏高度换算成 CSS 变量喂给页面。WebView 的 env(safe-area-inset-*)
        // 在部分机型上返回 0，必须用原生值兜底
        root.setOnApplyWindowInsetsListener(new View.OnApplyWindowInsetsListener() {
            @Override
            public WindowInsets onApplyWindowInsets(View v, WindowInsets insets) {
                try {
                    int top = insets.getSystemWindowInsetTop();
                    int bottom = insets.getSystemWindowInsetBottom();
                    if (top != lastTopInset || bottom != lastBottomInset) {
                        lastTopInset = top;
                        lastBottomInset = bottom;
                        pushSafeArea();
                    }
                } catch (Throwable ignored) {
                    // 取不到安全区就退回页面自己的 env()
                }
                return insets;
            }
        });

        webView = buildWebView();
        root.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        splashIcon = new ImageView(this);
        splashIcon.setImageResource(R.drawable.ic_splash);
        int size = Math.round(ICON_DP * getResources().getDisplayMetrics().density);
        root.addView(splashIcon, new FrameLayout.LayoutParams(size, size, Gravity.CENTER));

        setContentView(root);

        // 兜底再禁一次窗口开合动画，避免系统把整窗从侧边滑入
        overridePendingTransition(0, 0);

        // 布局完成后把缩放锚点钉在图标正中心，防止默认锚点偏移导致放大时跑位
        splashIcon.post(new Runnable() {
            @Override
            public void run() {
                splashIcon.setPivotX(splashIcon.getWidth() / 2f);
                splashIcon.setPivotY(splashIcon.getHeight() / 2f);
            }
        });

        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html");
        handler.postDelayed(revealTask, REVEAL_TIMEOUT_MS);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private WebView buildWebView() {
        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        WebView wv = new WebView(this);
        wv.setBackgroundColor(WINDOW_BG);
        wv.setAlpha(0f);
        wv.setTranslationY(pageOffsetPx);

        WebSettings settings = wv.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportZoom(false);
        settings.setMediaPlaybackRequiresUserGesture(false);

        wv.setWebViewClient(new WebViewClientCompat() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public void onPageCommitVisible(WebView view, String url) {
                pushSafeArea();
                reveal();
            }
        });

        // 页面里所有删除都走 window.confirm，WebView 默认不实现这个回调，
        // 不补上的话 confirm() 直接返回 false，删除逻辑当场中止
        wv.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onJsAlert(WebView view, String url, String message, final JsResult result) {
                AlertDialog.Builder b = new AlertDialog.Builder(MainActivity.this)
                        .setMessage(message)
                        .setPositiveButton("好", new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface d, int w) {
                                result.confirm();
                            }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            @Override
                            public void onCancel(DialogInterface d) {
                                result.cancel();
                            }
                        });
                showSafe(b, result);
                return true;
            }

            @Override
            public boolean onJsConfirm(WebView view, String url, String message, final JsResult result) {
                AlertDialog.Builder b = new AlertDialog.Builder(MainActivity.this)
                        .setMessage(message)
                        .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface d, int w) {
                                result.confirm();
                            }
                        })
                        .setNegativeButton("取消", new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface d, int w) {
                                result.cancel();
                            }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            @Override
                            public void onCancel(DialogInterface d) {
                                result.cancel();
                            }
                        });
                showSafe(b, result);
                return true;
            }

            @Override
            public boolean onJsPrompt(WebView view, String url, String message, String defaultValue,
                                      final JsPromptResult result) {
                final EditText input = new EditText(MainActivity.this);
                input.setInputType(InputType.TYPE_CLASS_TEXT);
                input.setText(defaultValue == null ? "" : defaultValue);
                input.setSelection(input.getText().length());
                AlertDialog.Builder b = new AlertDialog.Builder(MainActivity.this)
                        .setMessage(message)
                        .setView(input)
                        .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface d, int w) {
                                result.confirm(input.getText().toString());
                            }
                        })
                        .setNegativeButton("取消", new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface d, int w) {
                                result.cancel();
                            }
                        })
                        .setOnCancelListener(new DialogInterface.OnCancelListener() {
                            @Override
                            public void onCancel(DialogInterface d) {
                                result.cancel();
                            }
                        });
                showSafe(b, null);
                return true;
            }

            /**
             * <input type="file"> 在 WebView 里默认什么都不做，
             * 自定义牌面传图、导入学习集都依赖它，必须把选择结果原样回传。
             */
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (filePathCallback != null) {
                    filePathCallback.onReceiveValue(null);
                }
                filePathCallback = callback;
                try {
                    Intent intent = params.createIntent();
                    startActivityForResult(intent, REQ_FILE_CHOOSER);
                    return true;
                } catch (Throwable t) {
                    filePathCallback = null;
                    MemboApp.recordError(MainActivity.this, "onShowFileChooser", t);
                    return false;
                }
            }
        });
        // 页面通过它告知当前是深色还是浅色界面，用来切换状态栏图标明暗
        try {
            wv.addJavascriptInterface(new HostBridge(), "MemboHost");
        } catch (Throwable ignored) {
        }
        return wv;
    }

    /**
     * 全屏铺到底，系统栏透明。
     * 只用 SYSTEM_UI_FLAG_* 这套老标志，不引用 WindowInsetsController / DisplayCutout，
     * 那些高版本类型在某些 ROM 上执行到就会抛错，这也是上一版启动崩溃的原因。
     */
    private void setupEdgeToEdge() {
        try {
            Window w = getWindow();
            w.setStatusBarColor(Color.TRANSPARENT);
            w.setNavigationBarColor(Color.TRANSPARENT);
            applyBarStyle(false);
        } catch (Throwable t) {
            MemboApp.recordError(this, "setupEdgeToEdge", t);
            throw t;
        }
    }

    /** dark = true 时用浅色图标（页面是深底），false 用深色图标 */
    private void applyBarStyle(boolean dark) {
        int flags = View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION;
        if (!dark) {
            flags |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                    | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        }
        getWindow().getDecorView().setSystemUiVisibility(flags);
    }

    /** 降级方案：系统栏回到不透明，牺牲观感保住启动 */
    private void fallbackOpaqueBars() {
        try {
            Window w = getWindow();
            w.setStatusBarColor(WINDOW_BG);
            w.setNavigationBarColor(WINDOW_BG);
            w.getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                            | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        } catch (Throwable ignored) {
        }
    }

    /** 上次启动如果崩过，把堆栈直接显示出来，截个图就能定位 */
    private void showLastCrashIfAny() {
        try {
            File f = new File(getFilesDir(), MemboApp.CRASH_FILE);
            if (!f.exists()) {
                return;
            }
            byte[] buf = new byte[(int) f.length()];
            FileInputStream in = new FileInputStream(f);
            in.read(buf);
            in.close();
            f.delete();
            String text = new String(buf, "UTF-8").trim();
            if (text.isEmpty()) {
                return;
            }
            if (text.length() > 6000) {
                text = text.substring(0, 6000);
            }
            TextView tv = new TextView(this);
            tv.setText(text);
            tv.setTextSize(11);
            tv.setPadding(28, 24, 28, 24);
            ScrollView sc = new ScrollView(this);
            sc.addView(tv);
            new AlertDialog.Builder(this)
                    .setTitle("上次启动崩溃，请截图")
                    .setView(sc)
                    .setPositiveButton("知道了", null)
                    .show();
        } catch (Throwable ignored) {
        }
    }

    /** 把系统栏高度写进页面的 CSS 变量 */
    private void pushSafeArea() {
        if (webView == null || lastTopInset < 0) {
            return;
        }
        try {
            float d = getResources().getDisplayMetrics().density;
            String js = "(function(){var r=document.documentElement;"
                    + "r.style.setProperty('--safe-top-px','" + (lastTopInset / d) + "px');"
                    + "r.style.setProperty('--safe-bottom-px','" + (lastBottomInset / d) + "px');})()";
            webView.evaluateJavascript(js, null);
        } catch (Throwable ignored) {
        }
    }

    /** 暴露给页面的最小接口，只做状态栏明暗切换 */
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_FILE_CHOOSER) {
            if (filePathCallback == null) return;
            Uri[] results = null;
            if (resultCode == Activity.RESULT_OK && data != null) {
                try {
                    results = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
                } catch (Throwable t) {
                    results = null;
                }
            }
            filePathCallback.onReceiveValue(results);
            filePathCallback = null;
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    /** Android 10 及以上写 MediaStore，不需要任何存储权限 */
    private String writeToDownloadsModern(String name, byte[] bytes) throws Exception {
        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
        values.put(MediaStore.MediaColumns.MIME_TYPE, "application/json");
        values.put(MediaStore.MediaColumns.RELATIVE_PATH,
                Environment.DIRECTORY_DOWNLOADS + "/MemboX");
        Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new Exception("无法创建文件");
        OutputStream os = getContentResolver().openOutputStream(uri);
        if (os == null) throw new Exception("无法写入文件");
        try {
            os.write(bytes);
            os.flush();
        } finally {
            os.close();
        }
        return "下载/MemboX/" + name;
    }

    /** Android 9 及以下写应用私有目录，同样不需要权限 */
    private String writeToAppDir(String name, byte[] bytes) throws Exception {
        File dir = getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS);
        if (dir == null) dir = new File(getFilesDir(), "export");
        if (!dir.exists() && !dir.mkdirs()) throw new Exception("无法创建目录");
        File f = new File(dir, name);
        FileOutputStream fos = new FileOutputStream(f);
        try {
            fos.write(bytes);
            fos.flush();
        } finally {
            fos.close();
        }
        return f.getAbsolutePath();
    }

    public class HostBridge {
        /**
         * 页面导出的 JSON 写进本地文件。base64 由前端 btoa(unescape(encodeURIComponent(text))) 生成，
         * 全程不需要存储权限：Android 10+ 走 MediaStore，旧版本走应用私有目录。
         */
        @JavascriptInterface
        public void saveTextFile(final String filename, final String base64) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    String name = filename == null ? "" : filename.trim();
                    if (name.length() == 0) name = "membo-export.json";
                    name = name.replace("\\", "_").replace("/", "_").replace(":", "_")
                            .replace("*", "_").replace("?", "_").replace("\"", "_")
                            .replace("<", "_").replace(">", "_").replace("|", "_");
                    try {
                        byte[] bytes = Base64.decode(base64 == null ? "" : base64, Base64.DEFAULT);
                        String where = Build.VERSION.SDK_INT >= 29
                                ? writeToDownloadsModern(name, bytes)
                                : writeToAppDir(name, bytes);
                        Toast.makeText(MainActivity.this, "已导出到 " + where, Toast.LENGTH_LONG).show();
                    } catch (Throwable t) {
                        MemboApp.recordError(MainActivity.this, "saveTextFile", t);
                        Toast.makeText(MainActivity.this,
                                "导出失败：" + t.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }
            });
        }

        @JavascriptInterface
        public void setDarkChrome(final boolean dark) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    try {
                        applyBarStyle(dark);
                    } catch (Throwable ignored) {
                    }
                }
            });
        }
    }

    /** 弹窗期间 Activity 可能已经被系统回收，统一兜一下再展示 */
    private void showSafe(AlertDialog.Builder builder, JsResult result) {
        if (isFinishing() || isDestroyed()) {
            if (result != null) {
                result.cancel();
            }
            return;
        }
        try {
            builder.show();
        } catch (Exception e) {
            if (result != null) {
                result.cancel();
            }
        }
    }

    /**
     * 图标居中放大到消失，withEndAction 确认它已经不存在的那一帧，页面才开始淡入。
     * withLayer() 强制走硬件合成，缩放和透明度都在 GPU 上跑，不卡主线程。
     */
    private void reveal() {
        if (revealed) {
            return;
        }
        revealed = true;
        handler.removeCallbacks(revealTask);

        splashIcon.animate()
                .scaleX(ICON_SCALE)
                .scaleY(ICON_SCALE)
                .alpha(0f)
                .setDuration(ICON_MS)
                .setInterpolator(new DecelerateInterpolator(1.6f))
                .withLayer()
                .withEndAction(new Runnable() {
                    @Override
                    public void run() {
                        splashIcon.setVisibility(View.GONE);
                        startPageEnter();
                    }
                })
                .start();
    }

    /** 图标已彻底消失，这时才让页面进来，并通知页面播放字标浮起 */
    private void startPageEnter() {
        if (webView == null) {
            return;
        }
        webView.evaluateJavascript(
                "(function(){var v=document.getElementById('viewHome');if(!v){return;}"
                        + "v.classList.add('membo-enter');"
                        + "setTimeout(function(){v.classList.remove('membo-enter');},800);})()",
                null);

        // 只做透明度和微小位移。WebView 缩放会触发重新光栅化，掉帧的主因
        webView.animate()
                .alpha(1f)
                .translationY(0f)
                .setDuration(PAGE_MS)
                .setInterpolator(new DecelerateInterpolator(1.3f))
                .withLayer()
                .start();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView != null && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
