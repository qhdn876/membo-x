"""
把 Downloads 里的页面源文件构建成可发布的 web 目录。

做三件事：
  1. 复制源文件到 web/index.html
  2. 注入 PWA 所需的 head 标签（manifest、theme-color、图标、SW 注册）
  3. 幂等：重复执行不会叠加

用法：python tools/build_web.py
"""

import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path.home() / "Downloads" / "MEMORY-optimized.html"
WEB = ROOT.parent / "web"  # 发布目录放在仓库外，避免把 450KB 副本提交进 git
DST = WEB / "index.html"

START = "<!-- membo-pwa:start -->"
END = "<!-- membo-pwa:end -->"

BLOCK = f"""{START}
<link rel="manifest" href="./manifest.webmanifest" />
<meta name="theme-color" content="#ffffff" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Membo X" />
<link rel="icon" href="./icon.png" />
<link rel="apple-touch-icon" href="./apple-touch-icon.png" />
<script>
  if ('serviceWorker' in navigator) {{
    window.addEventListener('load', function () {{
      navigator.serviceWorker.register('./sw.js').catch(function () {{}});
    }});
  }}
</script>
{END}
</head>"""


def main() -> int:
    if not SRC.exists():
        print("找不到源文件:", SRC)
        return 1
    if not WEB.exists():
        print("找不到 web 目录:", WEB)
        return 1

    html = SRC.read_text(encoding="utf-8")
    html = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n</head>", "</head>", html, flags=re.S)

    if "</head>" not in html:
        print("源文件里没有 </head>")
        return 1
    html = html.replace("</head>", BLOCK, 1)
    DST.write_text(html, encoding="utf-8")

    title = re.search(r"<title>(.*?)</title>", html)
    desc = re.search(r'<meta name="description" content="(.*?)"', html)
    print("已生成:", DST)
    print("  标题:", title.group(1) if title else "缺失")
    print("  描述:", (desc.group(1)[:36] + "…") if desc else "缺失")
    print("  PWA 标签:", "manifest.webmanifest" in html)
    print("  文件大小:", len(html.encode()), "字节")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
