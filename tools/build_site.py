#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 Membo X 官网静态站点并打包为可上传到虚拟主机的 ZIP（解压即用）。"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
WEB = WORKSPACE / "web"
DOCS = ROOT / "docs"
DIST = WORKSPACE / "dist"
SRC_HTML = pathlib.Path.home() / "Downloads" / "MEMORY-optimized.html"
OUT = WORKSPACE / "site"
VER = "v1.0.12"

APK_NAME = f"MemboX-{VER}.apk"
HTML_NAME = f"MemboX-HTML-{VER}.html"
ZIP_NAME = f"MemboX-Web-PWA-{VER}.zip"

APK_SIZE = "348 KB"
HTML_SIZE = "509 KB"
PACKAGE = "com.membo.app"

# --------------------------------------------------------------------------
# 文案
# --------------------------------------------------------------------------
I18N = {
    "zh": {
        "lang": "zh-CN",
        "title": "Membo X · 本地记忆卡片工具 | 官网",
        "desc": "Membo X 是一款本地优先的记忆卡片工具。支持卡片翻转、左右滑动分类、收藏打乱，内置 Blast 记忆训练模式。免注册、无网络权限，数据只存本机。可在线体验，也可下载 Android APK。",
        "desc_short": "卡片翻转、左右滑动分类、收藏打乱、Blast 记忆训练。免注册、无网络权限，数据只存本机。",
        "kw": "记忆卡片,闪卡,抽认卡,背诵,记忆训练,学习工具,离线学习,Membo X,MemboX APK",
        "nav_features": "功能", "nav_shots": "截图", "nav_download": "下载",
        "nav_privacy": "隐私", "nav_faq": "常见问题",
        "lang_label": "EN", "lang_href": "./en.html",
        "lang_title": "Switch to English",
        "badge": "本地优先 · 免注册 · 完全离线",
        "h1a": "把要背的东西，", "h1b": "变成随手就能翻的卡片",
        "lead": "Membo X —— 一个只属于你本机的记忆卡片工具。打开就能背，关掉就走，数据从不离开设备。",
        "cta_online": "立即在线体验", "cta_apk": "下载 Android APK",
        "hero_note": "网页版无需安装 · APK 不申请任何系统权限",
        "s1v": "0", "s1l": "系统权限", "s2v": "0", "s2l": "联网请求",
        "s3v": "100%", "s3l": "数据在本机", "s4v": "免费", "s4l": "开源可用",
        "features_t": "为「记住」这件事，做减法",
        "features_s": "没有账号、没有同步、没有广告。只有一套顺手到不需要学习的记忆流程。",
        "f": [
            ("卡片翻转 · 重点高亮", "轻点卡片翻面查看释义，长按高亮关键词。正面提问、背面作答，符合最朴素的记忆规律。", "i-cards"),
            ("左右滑动 · 快速分类", "左滑「不熟悉」、右滑「熟悉」，支持撤回、洗牌、只练错词，几秒钟就能过完一组。", "i-swipe"),
            ("Blast 记忆训练", "把词条变成岩体，看题射击击碎目标。多段血量、分段节奏，换个方式把词记住。", "i-blast"),
            ("学习集管理", "自建学习集、批量导入词条、收藏常用卡片、隐藏暂时不练的内容，一切都在本地完成。", "i-stack"),
            ("外观自定义", "深浅主题、卡片背面透明度、字号与动效均可调整，按你的眼睛和设备来。", "i-theme"),
            ("零权限 · 无网络", "不声明任何 uses-permission，没有 INTERNET 权限，无第三方 SDK、无广告、无埋点。", "i-lock"),
        ],
        "shots_t": "真实界面，一看就会",
        "shots_s": "以下截图取自实际应用渲染，点击可查看大图。",
        "shot_cap": "记忆库 / 卡片学习 / Blast 训练",
        "dl_t": "选一个适合你的入口",
        "dl_s": "网页版与 APK 版的数据彼此独立（分别保存在浏览器与应用私有目录），可同时使用。",
        "dl_online_t": "网页版 · 在线体验",
        "dl_online_d": "直接在浏览器里打开，无需安装。支持手机与桌面浏览器，可添加到主屏幕当作 PWA 使用。",
        "dl_online_b": "打开在线版",
        "dl_apk_t": "Android 版 · APK",
        "dl_apk_d": "单文件安装即用的完整应用，零权限、可离线。适用于 Android 7.0 及以上。",
        "dl_apk_b": "下载 APK",
        "dl_html_t": "单文件 HTML · 离线版",
        "dl_html_d": "一个 HTML 文件包含全部功能，下载后双击即可用，也可以放进任意静态空间。",
        "dl_html_b": "下载 HTML",
        "dl_zip_t": "Web / PWA 完整包",
        "dl_zip_d": "含 manifest、Service Worker、图标与语言文件，可部署到自己的网站或托管平台。",
        "dl_zip_b": "下载 ZIP 包",
        "meta_ver": "版本", "meta_size": "大小", "meta_pkg": "包名",
        "priv_t": "隐私与安全",
        "priv_s": "这不是一句口号，而是写在 Manifest 里的技术事实。",
        "priv_rows": [
            ("网络访问", "未声明 INTERNET 权限，应用无法联网"),
            ("个人信息", "无账号体系，不收集姓名、手机号、邮箱等任何信息"),
            ("设备标识", "不读取 IMEI、MAC、Android ID 等标识"),
            ("数据存储", "仅使用应用私有目录，卸载应用即彻底删除"),
            ("第三方 SDK", "无统计、无广告、无推送、无崩溃上报"),
        ],
        "priv_more": "阅读完整隐私政策",
        "faq_t": "常见问题",
        "faq": [
            ("网页版和 APK 的数据互通吗？",
             "不互通。网页版的数据保存在浏览器本地存储，APK 版保存在应用私有目录，两者相互隔离。各自独立使用不受影响。"),
            ("需要联网吗？",
             "不需要。APK 版不声明网络权限；网页版首次加载后可离线使用（在 HTTPS 环境下可安装为 PWA，缓存完整资源）。"),
            ("支持哪些 Android 版本？",
             "Android 7.0（API 24）及以上。应用零权限，安装时不会弹出任何权限请求。"),
            ("如何备份学习数据？",
             "应用不提供云同步。可在系统设置中查看应用数据，或使用网页版的本地存储；卸载应用会一并清除本机数据。"),
        ],
        "foot_desc": "Membo X · 本地优先的记忆卡片工具",
        "foot_privacy": "隐私政策", "foot_source": "源代码", "foot_build": "版本 " + VER,
    },
    "en": {
        "lang": "en",
        "title": "Membo X · Local-First Flashcards | Official Site",
        "desc": "Membo X is a local-first flashcard tool with card flipping, swipe sorting, favorites, shuffling and a Blast training mode. No account, no network permission, all data stays on your device. Try it online or download the Android APK.",
        "desc_short": "Flip cards, swipe to sort, favorite and shuffle, plus Blast training. No account, no network permission, data stays on your device.",
        "kw": "flashcards, spaced repetition, memorization, study tool, offline learning, Membo X, MemboX APK",
        "nav_features": "Features", "nav_shots": "Screenshots", "nav_download": "Download",
        "nav_privacy": "Privacy", "nav_faq": "FAQ",
        "lang_label": "中文", "lang_href": "./index.html",
        "lang_title": "切换到中文",
        "badge": "Local-first · No sign-up · Fully offline",
        "h1a": "Turn what you need to remember", "h1b": "into cards you can flip anywhere",
        "lead": "Membo X is a flashcard tool that lives on your device. Open it, study, close it — your data never leaves the machine.",
        "cta_online": "Try it online", "cta_apk": "Download Android APK",
        "hero_note": "No install for the web version · The APK asks for zero permissions",
        "s1v": "0", "s1l": "permissions", "s2v": "0", "s2l": "network calls",
        "s3v": "100%", "s3l": "on-device data", "s4v": "Free", "s4l": "open source",
        "features_t": "Less noise, more remembering",
        "features_s": "No accounts, no sync, no ads. Just a study flow so simple you never have to learn it.",
        "f": [
            ("Flip cards & highlight", "Tap to reveal the answer and highlight key terms. Question on the front, answer on the back — the way memorization has always worked.", "i-cards"),
            ("Swipe to sort", "Swipe left for “again”, right for “known”. Undo, shuffle and practice missed cards in seconds.", "i-swipe"),
            ("Blast training", "Turn terms into rock targets and shoot them down. Multiple health levels and paced waves make review feel like a game.", "i-blast"),
            ("Deck management", "Create decks, add terms in bulk, favorite cards and hide what you are not studying — all offline.", "i-stack"),
            ("Make it yours", "Light and dark themes, card-back opacity, font size and motion are all adjustable.", "i-theme"),
            ("Zero permissions", "No uses-permission entries, no INTERNET permission, no third-party SDKs, no ads, no tracking.", "i-lock"),
        ],
        "shots_t": "Real screens, no mockups",
        "shots_s": "Every image below is captured from the actual app. Click any screenshot to enlarge it.",
        "shot_cap": "Deck list / Card study / Blast training",
        "dl_t": "Pick the entry point that fits you",
        "dl_s": "Web and APK keep separate data (browser storage vs. app-private storage), so you can use both.",
        "dl_online_t": "Web · Try online",
        "dl_online_d": "Open it straight in your browser — nothing to install. Works on mobile and desktop, and can be added to the home screen as a PWA.",
        "dl_online_b": "Open web version",
        "dl_apk_t": "Android · APK",
        "dl_apk_d": "A complete offline app with zero permissions. Requires Android 7.0 or newer.",
        "dl_apk_b": "Download APK",
        "dl_html_t": "Single-file HTML",
        "dl_html_d": "Everything in one HTML file. Download it, double-click to run, or host it anywhere.",
        "dl_html_b": "Download HTML",
        "dl_zip_t": "Web / PWA bundle",
        "dl_zip_d": "Includes the manifest, service worker, icons and locale files for your own hosting.",
        "dl_zip_b": "Download ZIP",
        "meta_ver": "Version", "meta_size": "Size", "meta_pkg": "Package",
        "priv_t": "Privacy by design",
        "priv_s": "Not a slogan — it is a technical fact declared in the app manifest.",
        "priv_rows": [
            ("Network access", "No INTERNET permission is declared; the app cannot go online"),
            ("Personal data", "No accounts; no name, phone number or email is collected"),
            ("Device identifiers", "No IMEI, MAC address or Android ID is read"),
            ("Data storage", "App-private directory only; uninstalling removes everything"),
            ("Third-party SDKs", "No analytics, ads, push notifications or crash reporting"),
        ],
        "priv_more": "Read the full privacy policy",
        "faq_t": "Frequently asked questions",
        "faq": [
            "Do the web version and APK share data?",
            "No. The web version uses browser local storage and the APK uses app-private storage, so they are isolated. Both work fine on their own.",
            "Do I need an internet connection?",
            "No. The APK has no network permission. The web version can be used offline after loading, and on HTTPS it can be installed as a PWA with full caching.",
            "Which Android versions are supported?",
            "Android 7.0 (API 24) and newer. The app requests zero permissions, so no permission dialogs appear during installation.",
            "How do I back up my cards?",
            "There is no cloud sync. Check the app data in system settings, or use the web version's local storage. Uninstalling the app removes its local data.",
        ],
        "foot_desc": "Membo X · A local-first flashcard tool",
        "foot_privacy": "Privacy policy", "foot_source": "Source code", "foot_build": "Version " + VER,
    },
}

# FAQ 在中文里是 (question, answer) 对，英文用扁平列表，统一成成对结构
FAQ_EN = [
    (I18N["en"]["faq"][0], I18N["en"]["faq"][1]),
    (I18N["en"]["faq"][2], I18N["en"]["faq"][3]),
    (I18N["en"]["faq"][4], I18N["en"]["faq"][5]),
    (I18N["en"]["faq"][6], I18N["en"]["faq"][7]),
]

CSS = """
:root { color-scheme: light; --blue:#2563eb; --ink:#1b2230; --muted:#6b7484; --line:#e8edf4; }
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body { margin:0; background:#f6f8fb; color:var(--ink); line-height:1.75;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }
a { color:var(--blue); }
img { max-width:100%; }

.nav { position:sticky; top:0; z-index:20; background:rgba(255,255,255,.92);
  backdrop-filter:blur(14px); border-bottom:1px solid var(--line); }
.nav-in { max-width:1120px; margin:0 auto; padding:13px 22px; display:flex; align-items:center; gap:24px; }
.logo { font-size:20px; font-weight:800; letter-spacing:1px; text-decoration:none; color:var(--ink); white-space:nowrap; }
.logo span { color:var(--blue); }
.nav-links { display:flex; gap:20px; flex-wrap:wrap; }
.nav-links a { color:#5b6577; text-decoration:none; font-size:14px; }
.nav-links a:hover { color:var(--blue); }
.spacer { flex:1; }
.lang { border:1px solid #dce3ee; border-radius:9px; padding:5px 11px; font-size:13px;
  text-decoration:none; background:#fff; white-space:nowrap; }

.hero { text-align:center; padding:66px 22px 12px; }
.badge { display:inline-block; padding:5px 14px; border-radius:999px; background:#eaf1ff;
  color:var(--blue); font-size:12.5px; font-weight:600; letter-spacing:.3px; }
.hero h1 { font-size:clamp(32px,6vw,54px); line-height:1.25; letter-spacing:1px; margin:18px 0 12px; }
.hero h1 b { color:var(--blue); font-weight:800; }
.lead { max-width:720px; margin:0 auto; color:#455063; font-size:17px; }
.desc { max-width:680px; margin:10px auto 0; color:var(--muted); font-size:14.5px; }
.cta { display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin:28px 0 10px; }
.btn { display:inline-flex; align-items:center; gap:8px; padding:12px 24px; border-radius:13px;
  font-size:15px; font-weight:700; text-decoration:none; border:1px solid #dce3ee;
  background:#fff; color:#243049; transition:transform .15s,box-shadow .15s; }
.btn:hover { transform:translateY(-2px); box-shadow:0 10px 26px rgba(30,50,90,.12); }
.btn.primary { background:linear-gradient(135deg,#2563eb,#4f7ff0); border-color:#2563eb; color:#fff; }
.btn svg { width:17px; height:17px; }
.note { font-size:12.5px; color:#98a1b0; margin:10px 0 0; }
.hero-shot { display:block; width:100%; max-width:900px; margin:34px auto 0; border-radius:18px;
  box-shadow:0 20px 50px rgba(24,39,75,.12); }

.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; max-width:900px; margin:44px auto 0; padding:0 22px; }
.stat { text-align:center; background:#fff; border:1px solid var(--line); border-radius:16px; padding:18px 10px; }
.stat b { display:block; font-size:25px; color:var(--blue); line-height:1.3; }
.stat span { font-size:13px; color:var(--muted); }

section.sec { max-width:1120px; margin:0 auto; padding:72px 22px 0; }
.sec-head { text-align:center; margin-bottom:32px; }
.sec-head h2 { font-size:clamp(24px,4vw,32px); margin:0 0 8px; letter-spacing:.5px; }
.sec-head p { color:var(--muted); margin:0; font-size:14.5px; }

.features { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }
.feature { background:#fff; border:1px solid var(--line); border-radius:18px; padding:24px;
  transition:transform .18s,box-shadow .18s; }
.feature:hover { transform:translateY(-3px); box-shadow:0 14px 34px rgba(16,24,40,.07); }
.feature .ico { width:44px; height:44px; border-radius:13px; background:#eef4ff; color:var(--blue);
  display:flex; align-items:center; justify-content:center; margin-bottom:14px; }
.feature .ico svg { width:23px; height:23px; }
.feature h3 { font-size:16px; margin:0 0 6px; }
.feature p { font-size:13.5px; color:var(--muted); margin:0; }

.shots { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:12px; }
.shots a { display:block; background:#fff; border:1px solid var(--line); border-radius:14px; overflow:hidden; }
.shots img { display:block; width:100%; height:auto; }
.shots a:hover { box-shadow:0 10px 26px rgba(16,24,40,.1); }

.dls { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:14px; }
.dl { background:#fff; border:1px solid var(--line); border-radius:18px; padding:24px; display:flex; flex-direction:column; }
.dl.featured { border:2px solid var(--blue); }
.dl h3 { font-size:17px; margin:0 0 8px; }
.dl p { font-size:13.5px; color:var(--muted); margin:0 0 18px; flex:1; }
.dl .btn { justify-content:center; padding:10px 18px; font-size:14px; }
.meta { font-size:12px; color:#8b93a1; margin:0 0 16px; line-height:1.9; }
.meta code { color:#5260a0; }

.priv-box { background:#fff; border:1px solid var(--line); border-radius:18px; padding:26px 30px; }
.priv-box table { width:100%; border-collapse:collapse; font-size:14px; }
.priv-box th,.priv-box td { border-bottom:1px solid #eef1f6; padding:11px 8px; text-align:left; vertical-align:top; }
.priv-box th { width:32%; color:#39445a; font-weight:600; }
.priv-box td { color:var(--muted); }
.priv-more { display:inline-block; margin-top:18px; font-size:14px; font-weight:600; text-decoration:none; }

.faq { display:grid; gap:10px; }
.faq details { background:#fff; border:1px solid var(--line); border-radius:14px; padding:2px 18px; }
.faq summary { cursor:pointer; font-weight:600; font-size:15px; padding:13px 0; list-style:none; }
.faq summary::-webkit-details-marker { display:none; }
.faq summary::after { content:"+"; float:right; color:var(--blue); font-size:18px; line-height:1; }
.faq details[open] summary::after { content:"\\2212"; }
.faq p { color:var(--muted); font-size:14px; margin:0 0 15px; }

footer { margin-top:74px; border-top:1px solid var(--line); padding:30px 22px 46px;
  text-align:center; font-size:13px; color:#8b93a1; }
footer a { text-decoration:none; }
footer .sep { margin:0 8px; color:#c9d0db; }

@media (max-width:720px) {
  .nav-links { display:none; }
  .hero { padding-top:44px; }
  .stats { grid-template-columns:repeat(2,1fr); }
  section.sec { padding-top:54px; }
  .priv-box { padding:20px 16px; }
  .priv-box th { width:38%; }
}
"""

SYMBOLS = """<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
<symbol id="i-cards" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="3" width="14" height="16" rx="2"/><path d="M4 7v12a2 2 0 0 0 2 2h10"/><path d="M10 8h6M10 12h4"/></symbol>
<symbol id="i-swipe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16M16 8l4 4-4 4M8 8L4 12l4 4"/></symbol>
<symbol id="i-blast" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></symbol>
<symbol id="i-stack" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="7" width="16" height="13" rx="2"/><path d="M7 4h10M7 12h10M7 16h6"/></symbol>
<symbol id="i-theme" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-lock" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/></symbol>
<symbol id="i-play" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></symbol>
<symbol id="i-down" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0l4-4m-4 4l-4-4M4 19h16"/></symbol>
</svg>"""

PRIVACY_EN = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Membo X · Privacy Policy</title>
<style>
:root { color-scheme: light; } * { box-sizing:border-box; }
body { margin:0; padding:48px 20px 80px; background:#f6f7f9; color:#1b1f24; line-height:1.8; font-size:15px;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }
main { max-width:720px; margin:0 auto; background:#fff; border-radius:18px; padding:40px 38px 46px;
  box-shadow:0 10px 40px rgba(16,24,40,.06); }
h1 { font-size:24px; margin:0 0 6px; } .meta { font-size:13px; color:#8b93a1; margin-bottom:30px; }
h2 { font-size:16px; margin:34px 0 10px; padding-left:11px; border-left:3px solid #2563eb; }
p,li { margin:8px 0; } ul { padding-left:22px; }
table { width:100%; border-collapse:collapse; margin:12px 0 6px; font-size:14px; }
th,td { border:1px solid #e6e9ef; padding:9px 12px; text-align:left; vertical-align:top; }
th { background:#f7f9fc; font-weight:500; }
code { background:#f1f3f7; padding:1px 6px; border-radius:5px; font-size:13px; }
.box { margin:22px 0; padding:16px 18px; border-radius:12px; background:#eef4ff; border:1px solid #d5e3ff; font-size:14px; }
footer { margin-top:40px; padding-top:18px; border-top:1px solid #eceff3; font-size:13px; color:#8b93a1; }
a { color:#2563eb; }
</style>
</head>
<body>
<main>
  <h1>Membo X Privacy Policy</h1>
  <div class="meta">
    App: Membo X　|　Package: com.membo.app<br>
    Effective: November 27, 2026　|　Last updated: November 27, 2026
  </div>
  <div class="box">In short: Membo X requests no system permissions, makes no network requests, and collects or uploads no personal information. All study data stays on your device and is deleted when you uninstall the app.</div>

  <h2>1. Information we collect</h2>
  <p>None. Membo X is a local-first flashcard tool. The decks, terms, progress and preferences you create are stored in your device's app-private storage and never leave it.</p>

  <h2>2. System permissions</h2>
  <table>
    <tr><th>Permission</th><th>Requested</th><th>Notes</th></tr>
    <tr><td>Internet</td><td>No</td><td>No INTERNET permission is declared; the app cannot access the network</td></tr>
    <tr><td>Camera</td><td>No</td><td>Not used</td></tr>
    <tr><td>Microphone</td><td>No</td><td>Not used</td></tr>
    <tr><td>Contacts</td><td>No</td><td>Not used</td></tr>
    <tr><td>Location</td><td>No</td><td>Not used</td></tr>
    <tr><td>Storage</td><td>No</td><td>No public storage access; only app-private files</td></tr>
    <tr><td>Device identifiers</td><td>No</td><td>No IMEI, MAC address or Android ID is read</td></tr>
  </table>
  <p>The app declares no <code>uses-permission</code> at all, so no permission dialog appears during installation.</p>

  <h2>3. Storage and deletion</h2>
  <ul>
    <li>All data is kept in the app's private directory on this device and is inaccessible to other apps.</li>
    <li>There is no account system, no sign-up and no cloud copy.</li>
    <li>Clearing app data in system settings, or deleting a deck inside the app, removes the corresponding content.</li>
    <li>Uninstalling the app removes its local data along with it. We neither can nor wish to retain it.</li>
  </ul>

  <h2>4. Third-party services</h2>
  <p>Membo X integrates no third-party SDKs, including analytics, crash reporting, advertising, social login or push services. There are no ads, no in-app purchases and no outbound links from inside the app.</p>

  <h2>5. Children's privacy</h2>
  <p>The app has no social, streaming, payment or content-distribution features and does not collect information from children. Because it collects no data at all, it is safe for minors to use.</p>

  <h2>6. Changes to this policy</h2>
  <p>If a future version adds network features or data collection, we will update this page and state it clearly in the release notes, and ask for your consent before enabling it.</p>

  <h2>7. Contact</h2>
  <p>Questions about this policy can be raised here:</p>
  <ul>
    <li>Project: <a href="https://github.com/qhdn876/membo-x" target="_blank" rel="noopener">github.com/qhdn876/membo-x</a></li>
    <li>Issues: <a href="https://github.com/qhdn876/membo-x/issues" target="_blank" rel="noopener">github.com/qhdn876/membo-x/issues</a></li>
  </ul>
  <footer>This policy matches the implementation inside Membo X. Source code: <a href="https://github.com/qhdn876/membo-x" target="_blank" rel="noopener">qhdn876/membo-x</a></footer>
</main>
</body>
</html>
"""

HTACCESS = """# Membo X 静态官网 —— 免费虚拟主机配置
# 若主机拒绝 .htaccess 中的某些指令导致 500，可直接删除本文件，站点仍可正常访问。

DirectoryIndex index.html

# 不列出目录内容
<IfModule mod_autoindex.c>
    IndexIgnore *
</IfModule>

# APK / ZIP 以二进制下载，而不是在浏览器里当文本打开
<IfModule mod_mime.c>
    AddType application/vnd.android.package-archive .apk
    AddType application/zip .zip
    AddType application/manifest+json .webmanifest
</IfModule>

# 下载文件强制另存为附件
<IfModule mod_headers.c>
    <FilesMatch "\\.(apk|zip)$">
        Header set Content-Disposition "attachment"
    </FilesMatch>
</IfModule>"""

# 只作用于 downloads/ 目录。根目录那份不能一并处理 html，
# 否则网站首页 index.html 也会变成"另存为"。
HTACCESS_DOWNLOADS = """# Membo X 下载目录：HTML 单文件包也走另存为
# 根目录 .htaccess 只拦 apk/zip，因为 html 全局拦截会把首页一起变成下载
<IfModule mod_headers.c>
    <FilesMatch "\\.html$">
        Header set Content-Disposition "attachment"
    </FilesMatch>
</IfModule>
"""

DEPLOY = """Membo X 官网 —— 部署说明
========================================

【一、上传到虚拟主机】
1. 解压 MemboX-Website-__VER__.zip。
2. 把解压出来的【全部文件和文件夹】上传到网站根目录，
   通常是 public_html / htdocs / www / 你的域名目录。
   注意：是把 index.html 等文件直接放进根目录，不是再套一层文件夹。
3. 浏览器打开 https://你的域名/ 即可看到首页。

【二、页面入口】
  首页（中文）        /index.html
  首页（英文）        /en.html
  在线体验 Web 版     /app/index.html
  下载 APK            /downloads/MemboX-__VER__.apk
  单文件 HTML         /downloads/MemboX-HTML-__VER__.html
  Web / PWA 完整包    /downloads/MemboX-Web-PWA-__VER__.zip
  隐私政策（中文）    /privacy.html
  隐私政策（英文）    /privacy-en.html

【三、常见问题】
Q：APK 点开变成乱码或在浏览器里显示文本？
A：说明主机没有正确设置 APK 的 MIME 类型。包内已附带 .htaccess 处理，
   若主机不支持 .htaccess，请在主机控制面板的「MIME 类型」中添加：
   .apk -> application/vnd.android.package-archive

Q：PWA「安装到主屏幕」不可用？
A：Service Worker 需要 HTTPS。免费主机若只提供 HTTP，在线体验本身
   完全正常，只是不能安装为 PWA。开启 HTTPS 后自动生效。

Q：免费主机有文件类型或容量限制？
A：整站约 4 MB，全部为静态文件（html/png/js/json/apk/zip），
   不需要 PHP、数据库或任何后端。

Q：能不能改域名或链接？
A：可以。所有站内链接均为相对路径，整体移动到任意目录仍能工作。
   唯一的外链是页脚的 GitHub 源码地址。

【四、更新版本】
替换 downloads/ 下的 APK / HTML 文件，并把 build_site.py 中的 VER
改为新版本号后重新运行，即可重新生成整站压缩包。
"""


def icon(kind: str) -> str:
    return f'<svg aria-hidden="true"><use href="#{kind}"/></svg>'


def render(lang: str) -> str:
    t = I18N[lang]
    faq = t["faq"] if lang == "zh" else FAQ_EN
    features = "".join(
        f'<div class="feature"><div class="ico">{icon(ico_id)}</div>'
        f'<h3>{title}</h3><p>{desc}</p></div>'
        for title, desc, ico_id in t["f"]
    )
    shot_files = ["02-sets.png", "03-study.png", "04-back.png",
                  "05-deck.png", "06-settings.png", "07-blast.png"]
    shots = "".join(
        f'<a href="./screenshots/{f}" target="_blank" rel="noopener">'
        f'<img src="./screenshots/{f}" alt="Membo X screenshot {i}"></a>'
        for i, f in enumerate(shot_files, 1)
    )
    priv_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in t["priv_rows"])
    faq_html = "".join(
        f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faq
    )
    stats = "".join(
        f'<div class="stat"><b>{t["s" + str(i) + "v"]}</b><span>{t["s" + str(i) + "l"]}</span></div>'
        for i in range(1, 5)
    )
    nav = [
        ("#features", t["nav_features"]), ("#screenshots", t["nav_shots"]),
        ("#download", t["nav_download"]), ("#privacy", t["nav_privacy"]),
        ("#faq", t["nav_faq"]),
    ]
    nav_html = "".join(f'<a href="{h}">{txt}</a>' for h, txt in nav)

    return f"""<!DOCTYPE html>
<html lang="{t['lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t['title']}</title>
<meta name="description" content="{t['desc']}">
<meta name="keywords" content="{t['kw']}">
<link rel="icon" href="./app/icon.png">
<style>{CSS}</style>
</head>
<body>
{SYMBOLS}
<header class="nav">
  <div class="nav-in">
    <a class="logo" href="./index.html">Membo<span>X</span></a>
    <nav class="nav-links">{nav_html}</nav>
    <span class="spacer"></span>
    <a class="lang" href="{t['lang_href']}" title="{t['lang_title']}">{t['lang_label']}</a>
  </div>
</header>

<main>
  <div class="hero">
    <span class="badge">{t['badge']}</span>
    <h1>{t['h1a']}<br><b>{t['h1b']}</b></h1>
    <p class="lead">{t['lead']}</p>
    <p class="desc">{t['desc_short']}</p>
    <div class="cta">
      <a class="btn primary" href="./app/index.html">{icon('i-play')}{t['cta_online']}</a>
      <a class="btn" href="./downloads/{APK_NAME}" download="{APK_NAME}">{icon('i-down')}{t['cta_apk']}</a>
    </div>
    <p class="note">{t['hero_note']}</p>
    <img class="hero-shot" src="./screenshots/overview.png" alt="Membo X interface overview">
  </div>

  <div class="stats">{stats}</div>

  <section class="sec" id="features">
    <div class="sec-head"><h2>{t['features_t']}</h2><p>{t['features_s']}</p></div>
    <div class="features">{features}</div>
  </section>

  <section class="sec" id="screenshots">
    <div class="sec-head"><h2>{t['shots_t']}</h2><p>{t['shots_s']}</p></div>
    <div class="shots">{shots}</div>
    <p class="note" style="text-align:center">{t['shot_cap']}</p>
  </section>

  <section class="sec" id="download">
    <div class="sec-head"><h2>{t['dl_t']}</h2><p>{t['dl_s']}</p></div>
    <div class="dls">
      <div class="dl featured">
        <h3>{t['dl_apk_t']}</h3><p>{t['dl_apk_d']}</p>
        <p class="meta">{t['meta_ver']}: <code>{VER}</code> · {t['meta_size']}: <code>{APK_SIZE}</code><br>
           {t['meta_pkg']}: <code>{PACKAGE}</code></p>
        <a class="btn primary" href="./downloads/{APK_NAME}" download="{APK_NAME}">{icon('i-down')}{t['dl_apk_b']}</a>
      </div>
      <div class="dl">
        <h3>{t['dl_online_t']}</h3><p>{t['dl_online_d']}</p>
        <a class="btn" href="./app/index.html">{icon('i-play')}{t['dl_online_b']}</a>
      </div>
      <div class="dl">
        <h3>{t['dl_html_t']}</h3><p>{t['dl_html_d']}</p>
        <p class="meta">{t['meta_size']}: <code>{HTML_SIZE}</code></p>
        <a class="btn" href="./downloads/{HTML_NAME}" download="{HTML_NAME}">{icon('i-down')}{t['dl_html_b']}</a>
      </div>
      <div class="dl">
        <h3>{t['dl_zip_t']}</h3><p>{t['dl_zip_d']}</p>
        <a class="btn" href="./downloads/{ZIP_NAME}" download="{ZIP_NAME}">{icon('i-down')}{t['dl_zip_b']}</a>
      </div>
    </div>
  </section>

  <section class="sec" id="privacy">
    <div class="sec-head"><h2>{t['priv_t']}</h2><p>{t['priv_s']}</p></div>
    <div class="priv-box">
      <table>{priv_rows}</table>
      <a class="priv-more" href="./{'privacy.html' if lang == 'zh' else 'privacy-en.html'}">{t['priv_more']} →</a>
    </div>
  </section>

  <section class="sec" id="faq">
    <div class="sec-head"><h2>{t['faq_t']}</h2></div>
    <div class="faq">{faq_html}</div>
  </section>
</main>

<footer>
  {t['foot_desc']} · {t['foot_build']}<br>
  <a href="./{'privacy.html' if lang == 'zh' else 'privacy-en.html'}">{t['foot_privacy']}</a>
  <span class="sep">·</span>
  <a href="https://github.com/qhdn876/membo-x" target="_blank" rel="noopener">{t['foot_source']}</a>
</footer>
</body>
</html>
"""


def build() -> pathlib.Path:
    for p in (WEB, DOCS, DIST, SRC_HTML):
        if not p.exists():
            raise SystemExit(f"缺少依赖: {p}")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "app").mkdir(parents=True)
    (OUT / "screenshots").mkdir()
    (OUT / "downloads").mkdir()

    # 页面
    (OUT / "index.html").write_text(render("zh"), encoding="utf-8")
    (OUT / "en.html").write_text(render("en"), encoding="utf-8")
    shutil.copyfile(DOCS / "privacy.html", OUT / "privacy.html")
    (OUT / "privacy-en.html").write_text(PRIVACY_EN, encoding="utf-8")
    (OUT / ".htaccess").write_text(HTACCESS, encoding="utf-8")
    (OUT / "DEPLOY.txt").write_text(DEPLOY.replace("__VER__", VER), encoding="utf-8")

    # 在线版、截图、下载文件
    shutil.copytree(WEB, OUT / "app", dirs_exist_ok=True)
    for f in sorted((DOCS / "screenshots").glob("*.png")):
        shutil.copyfile(f, OUT / "screenshots" / f.name)
    for src, name in [
        (DIST / APK_NAME, APK_NAME),
        (SRC_HTML, HTML_NAME),
        (DIST / ZIP_NAME, ZIP_NAME),
    ]:
        if not src.exists():
            raise SystemExit(f"缺少发布文件: {src}")
        shutil.copyfile(src, OUT / "downloads" / name)

    # 下载目录单独一份 .htaccess，让 HTML 单文件包也直接下载
    (OUT / "downloads" / ".htaccess").write_text(HTACCESS_DOWNLOADS, encoding="utf-8")

    # 打包：解压后内容直接位于站点根目录
    DIST.mkdir(exist_ok=True)
    archive = DIST / f"MemboX-Website-{VER}.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        # .htaccess 与说明优先，便于解压工具展示
        for f in [OUT / ".htaccess", OUT / "DEPLOY.txt", OUT / "index.html",
                  OUT / "en.html", OUT / "privacy.html", OUT / "privacy-en.html"]:
            z.write(f, f.name)
        for folder in ["app", "screenshots", "downloads"]:
            for f in sorted((OUT / folder).rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(OUT).as_posix())

    print(f"站点目录: {OUT}")
    print(f"压缩包:   {archive}  ({archive.stat().st_size:,} B)")
    n = sum(1 for f in OUT.rglob("*") if f.is_file())
    print(f"文件数:   {n}")
    return archive


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.parse_args()
    build()
