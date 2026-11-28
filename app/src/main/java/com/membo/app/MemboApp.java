package com.membo.app;

import android.app.Application;

import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintWriter;
import java.io.StringWriter;

/**
 * 兜底记录崩溃堆栈。写进 files 目录，下次启动由 MainActivity 读出来直接显示在屏幕上，
 * 不用连 adb 也能看到原因。
 */
public class MemboApp extends Application {

    public static final String CRASH_FILE = "last_crash.txt";

    /** 记录一次异常，下次启动会显示出来 */
    public static void recordError(android.content.Context ctx, String tag, Throwable error) {
        try {
            StringWriter writer = new StringWriter();
            writer.write("[" + tag + "]\n");
            error.printStackTrace(new PrintWriter(writer));
            File target = new File(ctx.getFilesDir(), CRASH_FILE);
            FileOutputStream out = new FileOutputStream(target);
            out.write(writer.toString().getBytes("UTF-8"));
            out.close();
        } catch (Throwable ignored) {
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();

        final Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() {
            @Override
            public void uncaughtException(Thread thread, Throwable error) {
                recordError(MemboApp.this, "uncaught", error);
                if (previous != null) {
                    previous.uncaughtException(thread, error);
                }
            }
        });
    }
}
