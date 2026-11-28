#!/usr/bin/env python3
"""
用 Edge 无头浏览器生成应用真实截图。

原理：从 Downloads 的源文件复制出若干临时 HTML，每个注入两小段脚本：
  1) 主脚本之前预置 localStorage 演示数据（多个学习集）
  2) 主脚本之后按场景点击真实按钮、并禁用 CSS 动画，让页面停在稳定状态
再用 Edge --headless --screenshot 截图。所有交互都是页面自身的事件，
不是另画的示意图，因此与真机界面一致。

用法：python tools/make_shots.py
"""

import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path.home() / "Downloads" / "MEMORY-optimized.html"
OUT = ROOT / "docs" / "screenshots"
TMP = ROOT.parent / "shots" / "_gen"

EDGE_CANDIDATES = [
    pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    pathlib.Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]

# 演示数据：保持中文界面，三个学习集，列表页不至于太空
SETS = [
    {
        "id": "s1", "title": "经络循行", "pinned": True, "updatedAt": 1764200000000,
        "cards": [
            {"id": "c1", "term": "胃", "def": "足阳明胃经，起于==鼻翼旁==，入上齿中", "fav": True, "hidden": False},
            {"id": "c2", "term": "三焦", "def": "三焦入耳==包眉梢==", "fav": True, "hidden": False},
            {"id": "c3", "term": "胆经", "def": "胆经络肝，在==眼耳边==", "fav": False, "hidden": False},
            {"id": "c4", "term": "心经", "def": "心络小肠肺，==食道与目系==", "fav": False, "hidden": False},
            {"id": "c5", "term": "膀胱", "def": "膀胱==肾脑眼==", "fav": False, "hidden": False},
            {"id": "c6", "term": "肺经", "def": "起于中焦，下络大肠，还循==胃口==", "fav": False, "hidden": False},
            {"id": "c7", "term": "肝经", "def": "抵小腹，挟胃，属肝络胆，贯膈布==胁肋==", "fav": False, "hidden": False},
            {"id": "c8", "term": "单面默想示例", "def": "", "fav": False, "hidden": False},
        ],
    },
    {
        "id": "s2", "title": "考研英语核心词", "pinned": False, "updatedAt": 1764190000000,
        "cards": [
            {"id": "e1", "term": "abandon", "def": "v. 放弃；抛弃", "fav": True, "hidden": False},
            {"id": "e2", "term": "elaborate", "def": "adj. 精心制作的 v. 详细阐述", "fav": False, "hidden": False},
            {"id": "e3", "term": "inevitable", "def": "adj. 不可避免的，必然的", "fav": False, "hidden": False},
            {"id": "e4", "term": "substantial", "def": "adj. 大量的；实质的", "fav": False, "hidden": False},
            {"id": "e5", "term": "trivial", "def": "adj. 琐碎的，不重要的", "fav": False, "hidden": False},
            {"id": "e6", "term": "versatile", "def": "adj. 多才多艺的；多用途的", "fav": False, "hidden": False},
        ],
    },
    {
        "id": "s3", "title": "古诗文默写", "pinned": False, "updatedAt": 1764180000000,
        "cards": [
            {"id": "p1", "term": "采菊东篱下", "def": "悠然见南山", "fav": False, "hidden": False},
            {"id": "p2", "term": "落霞与孤鹜齐飞", "def": "秋水共长天一色", "fav": False, "hidden": False},
            {"id": "p3", "term": "会当凌绝顶", "def": "一览众山小", "fav": False, "hidden": False},
            {"id": "p4", "term": "不以物喜", "def": "不以己悲", "fav": True, "hidden": False},
            {"id": "p5", "term": "山重水复疑无路", "def": "柳暗花明又一村", "fav": False, "hidden": False},
        ],
    },
]

STATE = {
    "sets": SETS,
    "customThemes": [],
    "mediaPool": [],
    "activeSetId": "s1",
    "settings": {"feedback": False},
}

SEED_SCRIPT = """<script id="membo-shot-seed">
(function () {
  try { localStorage.setItem('flow_memory_v2', %s); } catch (e) {}
})();
</script>
""" % json.dumps(json.dumps(STATE, ensure_ascii=False), ensure_ascii=False)

# 注意：上面故意做两层 json.dumps，外层生成合法的 JS 字符串字面量

# Edge 无头模式有最小视口宽度（这台机器是 479 CSS px），而 --window-size 指定
# 的截图宽度是 390 CSS px，右侧会被裁掉。给 html 加 transform 可让所有
# position:fixed 元素改为相对 html(390x844) 定位，从而精确还原手机布局。
CSS_KILL = """<style id="membo-shot-still">
*, *::before, *::after { animation: none !important; transition: none !important; }
html {
  width: 390px !important; height: 844px !important;
  overflow: hidden !important; transform: translateZ(0);
}
body { width: 390px !important; height: 844px !important; margin: 0 !important; overflow: hidden !important; }
.view { height: 100% !important; transition: none !important; }
#bzRoot { height: 100% !important; }
.view-inner { height: 100% !important; }
/* 卡片在 390 宽下按 9:14 排布，避免 aspect-ratio 把它撑出容器 */
#viewStudy .card-stack {
  width: 100% !important; max-width: 100% !important;
  height: auto !important; max-height: 100% !important; aspect-ratio: 9 / 14 !important;
}
#bzGameCanvas { width: 100% !important; height: 100% !important; }
.set-row, .mode-row, .card-list-item, .nav-entry-card { opacity: 1 !important; transform: none !important; }
#particle-canvas { display: none !important; }
</style>"""

BASE_JS = """(function () {
  function tap(id) { var el = document.getElementById(id); if (el) el.click(); }
  function row() { var r = document.querySelector('#setsContainer .set-row'); if (r) r.click(); }
  function key(k) { window.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true })); }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  setTimeout(async function () {
%s
  }, 80);
})();"""

STEPS = {
    # 启动品牌页
    "01-home": """    /* 停在首页 */""",
    # 记忆库列表
    "02-sets": """    tap('viewHome');
    await wait(120);""",
    # 卡片正面
    "03-study": """    tap('viewHome');
    await wait(80); row(); await wait(80);
    tap('btnEnterCardMode');
    await wait(200);""",
    # 卡片背面（按空格翻转，走页面真实的键盘监听）
    "04-back": """    tap('viewHome');
    await wait(80); row(); await wait(80);
    tap('btnEnterCardMode');
    await wait(200); key(' ');
    await wait(200);""",
    # 词库管理
    "05-deck": """    tap('viewHome');
    await wait(80); row(); await wait(80);
    tap('btnEnterCardMode');
    await wait(200); tap('btnDeck');
    await wait(200);""",
    # 设置面板
    "06-settings": """    tap('viewHome');
    await wait(80); row(); await wait(80);
    tap('btnEnterCardMode');
    await wait(200); tap('btnSettings');
    await wait(200);""",
    # Blast 训练模式
    "07-blast": """    tap('viewHome');
    await wait(80); row(); await wait(80);
    tap('btnEnterBlastMode');
    await wait(700);""",
}


def build_html(scene: str) -> str:
    html = SRC.read_text(encoding="utf-8")
    if "</head>" not in html:
        raise SystemExit("源文件缺少 </head>")
    html = html.replace("</head>", SEED_SCRIPT + "\n</head>", 1)
    tail = CSS_KILL + "\n<script>" + (BASE_JS % STEPS[scene]) + "</script>\n</body>"
    html = html.replace("</body>", tail, 1)
    return html


def find_edge() -> pathlib.Path:
    for p in EDGE_CANDIDATES:
        if p.exists():
            return p
    raise SystemExit("找不到 Edge 浏览器")


def make_overview() -> None:
    """把三张主界面拼成 README 首屏用的三联图（只加圆角与投影，不改动内容）。"""
    from PIL import Image, ImageDraw, ImageFilter

    names = ["02-sets.png", "03-study.png", "07-blast.png"]
    imgs = [Image.open(OUT / n).convert("RGB") for n in names]
    W, H = 940, 580
    ch = 470
    cw = round(ch * imgs[0].width / imgs[0].height)
    gap = 34
    x0 = (W - (3 * cw + 2 * gap)) // 2
    y0 = (H - ch) // 2

    bg = Image.new("RGB", (W, H), "#eef2f7")
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(246 - 12 * t), int(248 - 12 * t), int(251 - 10 * t)))
    bg = bg.convert("RGBA")

    radius = 20
    positions = [x0 + i * (cw + gap) for i in range(3)]

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for x in positions:
        sd.rounded_rectangle((x + 3, y0 + 8, x + cw + 3, y0 + ch + 8), radius,
                             fill=(24, 39, 75, 62))
    bg = Image.alpha_composite(bg, shadow.filter(ImageFilter.GaussianBlur(14)))

    for x, im in zip(positions, imgs):
        thumb = im.resize((cw, ch), Image.LANCZOS).convert("RGBA")
        mask = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), radius, fill=255)
        bg.paste(thumb, (x, y0), mask)

    dd = ImageDraw.Draw(bg)
    for x in positions:
        dd.rounded_rectangle((x, y0, x + cw - 1, y0 + ch - 1), radius,
                             outline=(210, 218, 230, 255), width=1)

    path = OUT / "overview.png"
    bg.convert("RGB").save(path, optimize=True)
    print("  OK    overview.png  %sB" % f"{path.stat().st_size:,}")


def main() -> int:
    if not SRC.exists():
        raise SystemExit("找不到源文件: %s" % SRC)
    edge = find_edge()
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    for scene, steps in STEPS.items():
        page = TMP / (scene + ".html")
        shot = OUT / (scene + ".png")
        page.write_text(build_html(scene), encoding="utf-8")
        profile = TMP / ("profile-" + scene)
        cmd = [
            str(edge),
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
            "--force-device-scale-factor=2",
            "--window-size=390,844",
            "--virtual-time-budget=5000",
            "--screenshot=" + str(shot),
            "--user-data-dir=" + str(profile),
            page.as_uri(),
        ]
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=90)
        ok = shot.exists() and shot.stat().st_size > 5000
        print(("  OK  " if ok else "  FAIL") + f"  {scene}.png"
              + (f"  {shot.stat().st_size:,}B" if ok else ""))
        if not ok:
            print("       ", (p.stderr or p.stdout).strip().splitlines()[-1][:160])
        shutil.rmtree(profile, ignore_errors=True)
    make_overview()
    print("\n产物目录:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
