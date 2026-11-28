"""
把 Downloads 里正在改的页面同步进 APK，并注入启动衔接样式。

每次改完 HTML 跑一次即可，重复执行不会叠加样式块。

用法：python tools/sync_page.py [源文件路径]
"""

import pathlib
import re
import sys

DEFAULT_SRC = pathlib.Path.home() / "Downloads" / "MEMORY-optimized.html"
DST = pathlib.Path("app/src/main/assets/index.html")

BLOCK = """<style id="membo-native">
  /* 安全区：WebView 的 env(safe-area-inset-*) 在部分机型返回 0，
     用原生注入的 --safe-*-px 兜底，两者取大值 */
  :root { --safe-top-px: 0px; --safe-bottom-px: 0px; }
  .view-inner,
  .sub-page-inner {
    padding-top: max(env(safe-area-inset-top, 0px), var(--safe-top-px));
    padding-bottom: max(env(safe-area-inset-bottom, 0px), var(--safe-bottom-px));
  }
  #bzRoot {
    --safe-top: max(env(safe-area-inset-top, 0px), var(--safe-top-px));
    --safe-bottom: max(env(safe-area-inset-bottom, 0px), var(--safe-bottom-px));
  }

  /* 原生启动衔接：图标完全消失后，页面淡入，首页字标同时浮起 */
  @keyframes memboRise {
    from { transform: translateY(14px) scale(0.94); }
    to   { transform: translateY(0) scale(1); }
  }
  #viewHome.membo-enter .home-center {
    animation: memboRise 0.5s cubic-bezier(0.2, 0.75, 0.2, 1) both;
  }
  @media (prefers-reduced-motion: reduce) {
    #viewHome.membo-enter .home-center { animation: none; }
  }
  /* 去掉长按选中与点击高亮的浏览器痕迹，贴近原生手感 */
  body { -webkit-tap-highlight-color: transparent; }
  input, textarea { -webkit-user-select: text; user-select: text; }
</style>
<script id="membo-native-chrome">
(function () {
  function lumOf(el) {
    var n = el;
    while (n && n.nodeType === 1) {
      var c = getComputedStyle(n).backgroundColor || '';
      var m = c.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
      if (m) {
        var a = m[4] === undefined ? 1 : parseFloat(m[4]);
        if (a > 0.5) return 0.299 * m[1] + 0.587 * m[2] + 0.114 * m[3];
      }
      n = n.parentElement;
    }
    return 255;
  }
  function sync() {
    var host = window.MemboHost;
    if (!host) return;
    var bz = document.getElementById('bzRoot');
    var blastOpen = !!bz && bz.style.display !== 'none';
    var v = document.querySelector('.view.active');
    var dark = blastOpen ? true : lumOf(v || document.body) < 140;
    try { host.setDarkChrome(dark); } catch (e) { /* 非容器环境忽略 */ }
  }
  function boot() {
    var obs = new MutationObserver(sync);
    document.querySelectorAll('.view').forEach(function (v) {
      obs.observe(v, { attributes: true, attributeFilter: ['class'] });
    });
    var bz = document.getElementById('bzRoot');
    if (bz) obs.observe(bz, { attributes: true, attributeFilter: ['style', 'class'] });
    if (document.body) obs.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    sync();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>
</head>"""


def main() -> int:
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src.exists():
        print("找不到源文件:", src)
        return 1

    html = src.read_text(encoding="utf-8")
    html = re.sub(r'<style id="membo-native">.*?</style>\n</head>', "</head>", html, flags=re.S)
    if "</head>" not in html:
        print("源文件里没有 </head>，结构变了")
        return 1

    # 目标文件比源文件新，说明有人直接改过 assets 里的副本，提醒一下再覆盖
    if DST.exists() and DST.stat().st_mtime > src.stat().st_mtime + 1:
        print("注意：assets/index.html 比源文件新，可能有直接改动会被覆盖")
        print("      如果确实改的是 assets 那份，先把它复制回源文件")

    html = html.replace("</head>", BLOCK, 1)
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(html, encoding="utf-8")

    print("源文件 :", src, "->", len(html), "字节")
    print("已写入 :", DST)
    print("样式块 :", "membo-native" in html, "| 字标:", re.search(r'home-logo">(.+?)</h1>', html).group(1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
