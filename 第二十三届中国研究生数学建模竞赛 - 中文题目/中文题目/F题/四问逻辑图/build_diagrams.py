"""Build two editable draw.io diagrams and matching SVG previews.

The diagram wording follows the four supplied F-question notebooks.  SVG and
draw.io are generated from the same drawing commands so their content matches.
"""

from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from pathlib import Path


OUT = Path(__file__).resolve().parent
FONT = "Microsoft YaHei,Arial,sans-serif"
NAVY = "#203650"
BLUE = "#315b84"
BLUE_LIGHT = "#eaf3fa"
TEAL = "#2f746f"
TEAL_LIGHT = "#e9f5f1"
ORANGE = "#a05e2b"
ORANGE_LIGHT = "#fff2e8"
PURPLE = "#665894"
PURPLE_LIGHT = "#f0eef8"
MUTED = "#607086"
LINE = "#b8c7d6"
WHITE = "#ffffff"
BG = "#f6f8fb"


class Figure:
    def __init__(self, width: int, height: int, title: str, bg: str = BG,
                 type_scale: bool = True):
        self.w, self.h, self.title = width, height, title
        self.bg = bg
        self.type_scale = type_scale
        self.shapes: list[tuple] = []
        self.edges: list[tuple] = []
        self.n = 0

    def _id(self, prefix: str) -> str:
        self.n += 1
        return f"{prefix}_{self.n:03d}"

    def rect(self, x, y, w, h, fill=WHITE, stroke="none", radius=0, sw=1):
        self.shapes.append(("rect", self._id("box"), x, y, w, h, fill, stroke, radius, sw))

    def label(self, x, y, w, h, lines, size=17, color=NAVY, bold=False,
              align="left", valign="middle"):
        if isinstance(lines, str):
            lines = lines.split("\n")
        # Keep a simple three-level type scale in both export formats.
        if self.type_scale:
            size = 28 if size >= 30 else 22 if size >= 22 else 16
        self.shapes.append(("text", self._id("txt"), x, y, w, h, list(lines), size,
                            color, bold, align, valign))

    def arrow(self, points, color=BLUE, width=2.5, dash=False, end=True):
        self.edges.append((self._id("edge"), list(points), color, width, dash, end))

    def pill(self, x, y, w, h, title, fill, color=WHITE, size=17):
        self.rect(x, y, w, h, fill=fill, radius=13)
        self.label(x + 6, y + 1, w - 12, h - 2, title, size=size, color=color,
                   bold=True, align="center")

    def card(self, x, y, w, h, fill=WHITE, stroke="none", radius=17):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, radius=radius, sw=1.2)

    def save(self, stem: str):
        self._save_svg(OUT / f"{stem}.svg")
        self._save_drawio(OUT / f"{stem}.drawio", stem)
        self._save_html(OUT / f"{stem}.html", stem)

    def _save_svg(self, path: Path):
        svg = ET.Element("svg", {
            "xmlns": "http://www.w3.org/2000/svg", "width": str(self.w),
            "height": str(self.h), "viewBox": f"0 0 {self.w} {self.h}",
        })
        defs = ET.SubElement(svg, "defs")
        for color in [BLUE, TEAL, ORANGE, PURPLE, MUTED, NAVY]:
            marker = ET.SubElement(defs, "marker", {
                "id": f"arrow-{color[1:]}", "markerWidth": "9", "markerHeight": "9",
                "refX": "8", "refY": "4.5", "orient": "auto",
                "markerUnits": "userSpaceOnUse",
            })
            ET.SubElement(marker, "path", {"d": "M0,0 L9,4.5 L0,9 Z", "fill": color})
        ET.SubElement(svg, "rect", {"x": "0", "y": "0", "width": str(self.w),
                                    "height": str(self.h), "fill": self.bg})
        for _, points, color, width, dash, end in self.edges:
            attrs = {
                "points": " ".join(f"{x},{y}" for x, y in points),
                "fill": "none", "stroke": color, "stroke-width": str(width),
                "stroke-linecap": "round", "stroke-linejoin": "round",
            }
            if dash:
                attrs["stroke-dasharray"] = "7 6"
            if end:
                attrs["marker-end"] = f"url(#arrow-{color[1:]})"
            ET.SubElement(svg, "polyline", attrs)
        for shape in self.shapes:
            if shape[0] == "rect":
                _, _, x, y, w, h, fill, stroke, radius, sw = shape
                ET.SubElement(svg, "rect", {
                    "x": str(x), "y": str(y), "width": str(w), "height": str(h),
                    "rx": str(radius), "ry": str(radius), "fill": fill,
                    "stroke": stroke, "stroke-width": str(sw),
                })
            else:
                _, _, x, y, w, h, lines, size, color, bold, align, valign = shape
                anchor = {"left": "start", "center": "middle", "right": "end"}[align]
                tx = x + (0 if align == "left" else w / 2 if align == "center" else w)
                line_h = size * 1.35
                ty = y + (h - (len(lines) - 1) * line_h) / 2 + size * 0.35
                if valign == "top":
                    ty = y + size
                t = ET.SubElement(svg, "text", {
                    "x": str(tx), "y": str(ty), "font-family": FONT,
                    "font-size": str(size), "font-weight": "700" if bold else "400",
                    "fill": color, "text-anchor": anchor,
                })
                for i, line in enumerate(lines):
                    sp = ET.SubElement(t, "tspan", {"x": str(tx), "dy": "0" if i == 0 else str(line_h)})
                    sp.text = line
        path.write_bytes(ET.tostring(svg, encoding="utf-8", xml_declaration=True))

    def _save_drawio(self, path: Path, name: str):
        mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "agent": "Codex",
                                        "version": "24.7.17", "pages": "1"})
        diagram = ET.SubElement(mxfile, "diagram", {"id": name, "name": self.title})
        model = ET.SubElement(diagram, "mxGraphModel", {
            "dx": str(self.w), "dy": str(self.h), "grid": "0", "gridSize": "10",
            "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
            "fold": "1", "page": "1", "pageScale": "1",
            "pageWidth": str(self.w), "pageHeight": str(self.h),
            "background": self.bg, "math": "0", "shadow": "0",
        })
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        for eid, points, color, width, dash, end in self.edges:
            style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;"
                     f"strokeColor={color};strokeWidth={width};"
                     f"dashed={1 if dash else 0};dashPattern=7 6;"
                     f"endArrow={'block' if end else 'none'};endFill=1;endSize=8;")
            edge = ET.SubElement(root, "mxCell", {
                "id": eid, "value": "", "style": style, "edge": "1", "parent": "1",
            })
            geom = ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})
            ET.SubElement(geom, "mxPoint", {"x": str(points[0][0]),
                                            "y": str(points[0][1]), "as": "sourcePoint"})
            ET.SubElement(geom, "mxPoint", {"x": str(points[-1][0]),
                                            "y": str(points[-1][1]), "as": "targetPoint"})
            if len(points) > 2:
                arr = ET.SubElement(geom, "Array", {"as": "points"})
                for x, y in points[1:-1]:
                    ET.SubElement(arr, "mxPoint", {"x": str(x), "y": str(y)})
        for shape in self.shapes:
            if shape[0] == "rect":
                _, sid, x, y, w, h, fill, stroke, radius, sw = shape
                style = (f"rounded={1 if radius else 0};arcSize={radius};html=1;"
                         f"fillColor={fill};strokeColor={stroke};strokeWidth={sw};")
                value = ""
            else:
                _, sid, x, y, w, h, lines, size, color, bold, align, valign = shape
                style = ("text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;"
                         f"fontFamily=Microsoft YaHei;fontSize={size};fontColor={color};"
                         f"fontStyle={1 if bold else 0};align={align};"
                         f"verticalAlign={valign};spacing=0;overflow=hidden;")
                value = "<br>".join(html.escape(line) for line in lines)
            cell = ET.SubElement(root, "mxCell", {"id": sid, "value": value,
                                                  "style": style, "vertex": "1", "parent": "1"})
            ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y),
                                               "width": str(w), "height": str(h), "as": "geometry"})
        path.write_bytes(ET.tostring(mxfile, encoding="utf-8", xml_declaration=True))

    def _save_html(self, path: Path, stem: str):
        path.write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>@page {{ size: {self.w / 96:.4f}in {self.h / 96:.4f}in; margin: 0; }}
html,body {{ width:{self.w}px;height:{self.h}px;margin:0;overflow:hidden;background:{self.bg}; }}
img {{display:block;width:{self.w}px;height:{self.h}px;}}</style></head>
<body><img src="{stem}.svg"></body></html>''', encoding="utf-8")


def logic_diagram():
    f = Figure(1800, 1190, "四问论证逻辑流程图")
    f.label(56, 25, 1100, 57, "四问论证逻辑流程图", 31, NAVY, True)
    f.label(57, 81, 1460, 29,
            "左侧证据进入主论证链；右侧标出结论的适用边界；向下箭头表示跨问传递", 18, MUTED)
    f.pill(1494, 34, 249, 39, "以修订版第二问为准", BLUE, WHITE, 16)

    rows = [151, 391, 631, 871]
    colors = [BLUE, TEAL, ORANGE, PURPLE]
    lights = [BLUE_LIGHT, TEAL_LIGHT, ORANGE_LIGHT, PURPLE_LIGHT]
    heads = [
        "问题一  数据质量与领域配比",
        "问题二  从经典标度律到广义损失",
        "问题三  预算约束下的联合资源配置",
        "问题四  历史能力前沿与条件预测",
    ]
    evidence = [
        ["A1–A3：质量指标", "A4–A15：配比—Loss", "A16：领域映射"],
        ["B1：标度律拟合", "B2–B5：外部验证", "B6/B7：质量证据"],
        ["Q1：可执行配比候选", "Q2：广义损失函数", "C7：上下文可行域"],
        ["C1–C4：能力/训练算力", "C8：逐任务记录", "C5/C6：桥接样本"],
    ]
    premises = [
        "前提：质量指标有冲突；训练配比影响平均 Loss",
        "前提：B1 给出规模骨架；Q_i、p 由问题一提供",
        "前提：广义损失是目标；预算与上下文给出约束",
        "前提：历史能力与算力记录可刻画经验前沿",
    ]
    arguments = [
        "推理：冲突消解得 Q_res；SCI 均值预测＋MPR-MTL 风险评估",
        "推理：L = E + R(N,D) × ψ_Q^rel(Q,p) × ψ_p(p,N)",
        "推理：在有限可执行 p 集合中联合优化 N、D、Q",
        "推理：q90 归因；C5→C6 桥接；3 月滚动回测",
    ]
    conclusions = [
        "结论：17 域 Q_i，p_risk / p_safe 等候选",
        "结论：L(N,D,Q,p)；边际效用与替代条件",
        "结论：(N*,D*,Q*,p*)、L*(C) 与 R0/R1/R2 转移",
        "结论：能力归因及 12/24 月前沿情景",
    ]
    boundaries = [
        ["SCI 是问题一的均值预测器", "质量加权份额 η=0", "新配比尚无独立实测 Loss"],
        ["主配比桥是对数模型", "SCI 未进入第二问主公式", "γ_p 未识别，名义取 0"],
        ["仅为候选集合内的模型最优", "高预算结果为远距离外推"],
        ["Q3 的 ΔL* 只做增量核对", "长期预测未获直接回测", "3 月未优于 Persistence"],
    ]
    handoffs = ["Q_i、p 候选与配比结构", "广义损失与参数边界", "ΔL*：条件性辅助核对"]

    for i, y in enumerate(rows):
        color, light = colors[i], lights[i]
        f.card(62, y + 26, 384, 128, fill=light, radius=16)
        f.label(79, y + 35, 350, 28, "证据输入", 16, color, True)
        f.label(79, y + 70, 350, 78, evidence[i], 16, NAVY, valign="top")

        f.card(502, y, 810, 180, fill=WHITE, radius=17)
        f.rect(502, y, 810, 43, fill=color, radius=15)
        f.rect(502, y + 26, 810, 17, fill=color)
        f.label(524, y + 3, 766, 36, heads[i], 22, WHITE, True)
        f.label(529, y + 57, 760, 27, premises[i], 17, NAVY)
        f.label(529, y + 96, 760, 27, arguments[i], 17, NAVY)
        f.rect(522, y + 136, 770, 1, fill="#e2e9ef")
        f.label(529, y + 145, 760, 27, conclusions[i], 17, color, True)

        f.card(1360, y + 19, 378, 142, fill="#eef2f6", radius=16)
        f.label(1378, y + 29, 343, 27, "适用边界", 16, MUTED, True)
        f.label(1378, y + 66, 343, 91, boundaries[i], 16, MUTED, valign="top")
        f.arrow([(449, y + 90), (493, y + 90)], color=color, width=2.7)
        f.arrow([(1317, y + 90), (1351, y + 90)], color=MUTED, width=2.2)

        if i < 3:
            f.arrow([(907, y + 184), (907, rows[i + 1] - 8)],
                    color=colors[i + 1], width=3, dash=(i == 2))
            f.pill(949, y + 192, 345, 34, handoffs[i], lights[i + 1],
                   colors[i + 1], 16)

    f.rect(62, 1095, 1676, 1, fill=LINE)
    f.label(65, 1108, 1670, 59,
            ["主论证链：Q_res 与配比候选 → L(N,D,Q,p) → 预算内最优配置。",
             "问题四以 C 系列历史证据为主，Q3 的 ΔL* 仅用于锚定的条件性核对。"],
            17, NAVY, bold=True, valign="top")
    f.save("四问论证逻辑图")


def technical_route_diagram():
    """Dense evidence-to-claim route, matching the user's text-chain reference."""
    bg = "#101214"
    row_bg = "#26292c"
    gray = "#d5d9dd"
    subtle = "#aab4bd"
    qcols = ["#62b5d4", "#6bc9af", "#e1ab69", "#b4a0e6"]
    f = Figure(2600, 2180, "四问论证技术路线", bg=bg, type_scale=False)
    f.rect(31, 26, 5, 102, fill=qcols[0])
    f.label(86, 27, 1690, 67, "四问论证技术路线", 36, "#eceff2", True)
    f.label(88, 98, 2350, 35,
            "每行写明：证据从哪里来 → 经何种推理或验证 → 得到什么结论；过渡带写明跨问传递的量与假设。",
            22, subtle)

    def section(y: int, qi: int, title: str, rows: list[tuple[str, str]]):
        col = qcols[qi - 1]
        f.rect(37, y + 7, 5, 462 if qi == 1 else 407 if qi == 2 else 302 if qi == 3 else 354,
               fill=col)
        f.rect(85, y, 84, 40, fill=col, radius=7)
        f.label(91, y + 2, 72, 34, f"Q{qi}", 26, bg, True, align="center")
        f.label(187, y + 1, 2190, 40, title, 26, "#e5e9ed", True)
        first = y + 53
        for j, (tag, claim) in enumerate(rows):
            ry = first + j * 52
            f.rect(86, ry, 2430, 46, fill=row_bg, radius=5)
            f.label(101, ry + 1, 169, 44, tag, 22, col, True)
            f.label(280, ry + 1, 2200, 44, claim, 22, gray)

    def bridge(y: int, color: str, lines: list[str]):
        f.rect(86, y, 2430, 78, fill="#1c3137" if color == qcols[1]
               else "#352b22" if color == qcols[2] else "#2c2839", radius=9)
        f.label(112, y + 9, 2380, 61, lines, 22, "#e5e9ed", True)

    section(153, 1, "第一问｜从原始数据到质量评分、配比预测与可传递接口", [
        ("质量输入", "A1 全量抽样＋A2/A3 扩展全集 → 22 项质量指标 → 方向统一与截尾归一化 → 线性评分 Q_lin"),
        ("冲突消解", "严格互斥的高/低尾部 → 指标对冲突与四维失衡 CI → 加权几何聚合 → 样本质量 Q_res"),
        ("独立复核", "A2/A3 中与 A1 ID 不重叠的余集 → 冻结尾部切点复核；去重聚合 → 7 个质量域 Q_d"),
        ("质量映射", "A16 的领域关系 → 7 个质量域映射到 17 个配方域 Q_i；无直接映射的 11 域作均值回退"),
        ("配比模型", "A4/A5：512 组配比 × 13 验证域 Loss → 对数线性／SCM → 训练侧稳定筛选 SCI → 均值预测"),
        ("配比推荐", "SCI 均值＋MPR-MTL 逐域残差 → CVaR 风险推荐 p_risk；凸包内双代理保守推荐 → p_safe"),
        ("固定检验", "A6–A11：1M／60M／1B 排序检验；A12–A15：10B／70B 幂律外推表，只作敏感性分析"),
        ("关键判断", "质量有效份额 p_eff∝p·Q_i^η 的内部验证选 η=0 → Q_i 与 p 分通道，不宣称 A 已识别质量效应"),
    ])
    bridge(634, qcols[1], [
        "Q1 → Q2：第一问最终输出 Q_i＝Q_res 的域映射与 p_risk；旧版 Q1 输出对数混料系数及参考配比 p_ref。",
        "模型角色：SCI 是 Q1 的均值预测器；Q2 为得到可解析的配比桥改用对数模型。p_safe 另由 Q1 直接进入 Q3。",
    ])
    f.arrow([(60, 617), (60, 729)], color=qcols[1], width=3)

    section(735, 2, "第二问｜先识别规模与质量效应，再把第一问的 Q、p 接入广义标度律", [
        ("规模骨架", "B1 轨迹 → 拟合经典 L＝E＋A·N^−α＋B·D^−β → 规模项 R(N,D)；B2–B5 检验迁移"),
        ("质量效应", "B6 比较质量项形式并估计 κ；B7 新质量水平作外层验证；B8 只作机制边界分析"),
        ("Q 的衔接", "Q1 的 Q_i 与配比 p → Q0_A(p)＝Σp_iQ_i；Q_A＝Q_res 经坐标桥映射到 B 的 Q_B"),
        ("避免重计", "以 Q0_A(p) 为当前配比的质量基线 → ψ_Q^rel(Q,p)＝ψ_Q^abs(Q)／ψ_Q^abs(Q0_A(p))"),
        ("p 的衔接", "Q1 对数混料 L_mix(p)／L_mix(p_ref) → ψ_p(p,N)；SCI 稳定交互只作辅助证据"),
        ("识别边界", "A6–A9 同配比跨规模排序可复核结构，但 γ_p 不可单独识别 → 名义 γ_p＝0＋情景敏感性"),
        ("广义结论", "L＝E＋R(N,D)·ψ_Q^rel(Q,p)·ψ_p(p,N) → 边际效用／替代条件；B9/B10 仅条件外推"),
    ])
    bridge(1166, qcols[2], [
        "Q2 → Q3：传 L(N,D,Q,p)、质量基线 Q0_A(p)、κ、配比桥及 γ_p 未识别标记；不能把名义 γ_p 当实测。",
        "Q3 同时从 Q1 读取可执行 p_risk／p_safe／p_measured；p_ref 只是第二问标度律的参考配比。",
    ])
    f.arrow([(60, 1148), (60, 1257)], color=qcols[2], width=3)

    section(1263, 3, "第三问｜把广义损失变成预算内资源决策，而非再估计 Q 或配比规律", [
        ("决策集合", "Q1 配比候选＋Q2 广义损失 → p 取有限可执行集合；p_ref 仅比较基准，不参加最优解"),
        ("成本约束", "训练成本 6ND＋注意力开销＋质量治理成本；C7 定外生上下文 L_ctx 与注意力临界值"),
        ("联合寻优", "三档预算 10^19／10^22／10^24；三类质量成本 → 枚举配比与活跃约束，联合求 N、D、Q"),
        ("结构转移", "Q＝Q0 为 R0，内部质量治理为 R1，Q＝1 为 R2 → 连续预算扫描识别体制变化"),
        ("结果边界", "输出 (N*,D*,Q*,p*) 与 L*(C)，再作成本／上下文／情景稳健性；高预算标为远距离外推"),
    ])
    bridge(1590, qcols[3], [
        "Q3 → Q4：只传最优损失增量 ΔL*＝L*(C₀)−L*(C₁) 作条件性核对，不把绝对 Loss 当绝对能力分。",
        "Q4 的能力前沿主证据仍来自 C 系列历史记录；Loss–Benchmark 转换须由 C5/C6 单独校准与验证。",
    ])
    f.arrow([(60, 1572), (60, 1681)], color=qcols[3], width=3, dash=True)

    section(1687, 4, "第四问｜历史能力证据为主，第三问最优损失只提供一条旁证通道", [
        ("能力定义", "C1 六维榜单 → 综合能力 S／模型类型／开源口径；C8 逐任务重建综合分并检验异质性"),
        ("规模归因", "C1×C4 匹配训练算力 → Compute-Q90 前沿；按发布时间做算力／非规模时间漂移／残差分解"),
        ("长期背景", "C3：2019–2025 时代视角；C4 变化点与训练算力增长率 → 延续／放缓／停滞情景"),
        ("桥接验证", "C5 校准自适应 Loss–Benchmark Logistic 桥；C6 新增模型外层验证，再用 C6 全量重估"),
        ("增量核对", "Q3 的 ΔL*＋当前实测前沿 F0 → 锚定的能力增量；大部分目标预算需远距离外推"),
        ("预测证据", "有效滚动回测仅 3 个月，且无前沿刷新；与 Persistence 比较 → 12／24 月只报长期情景"),
    ])
    f.rect(86, 2076, 2430, 1, fill="#4b5862")
    f.label(87, 2091, 2428, 57,
            ["全链条：A 中质量与配比证据 → B 中 N、D、Q、p 的损失律 → C7 下的预算最优解 → C 历史前沿与条件预测。",
             "证据边界：SCI 未成为 Q2 主配比桥；γ_p 未识别；Q3 最优是模型内结论；Q4 长期预测没有直接回测。"],
            22, subtle, valign="top")
    f.save("四问论证逻辑图")


def flow_diagram():
    f = Figure(1800, 1100, "四问整体流程")
    f.label(55, 27, 1120, 53, "四问整体流程图", 31, NAVY, True)
    f.label(56, 84, 1530, 27,
            "每一问按“输入 → 计算 → 验证 → 交付”推进；竖向箭头表示传给下一问的接口", 18, MUTED)
    x_stage, x_in, x_do, x_check, x_out = 52, 255, 570, 1118, 1438
    w_stage, w_in, w_do, w_check, w_out = 172, 284, 516, 284, 302
    ys = [157, 385, 613, 841]
    colors = [BLUE, TEAL, ORANGE, PURPLE]
    lights = [BLUE_LIGHT, TEAL_LIGHT, ORANGE_LIGHT, PURPLE_LIGHT]
    stage_titles = ["问题一", "问题二", "问题三", "问题四"]
    stage_subs = ["定义数据", "构造规律", "做出决策", "检验前沿"]
    inputs = [
        ["A1–A3：质量记录", "A4–A15：配比与 Loss", "A16：领域映射"],
        ["Q1：Q_i、配比与结构桥", "B1–B10：标度与质量数据"],
        ["Q1：可执行候选 p", "Q2：L(N,D,Q,p)", "C7：上下文可行域"],
        ["C1–C4/C8：历史能力", "C5/C6：桥接样本", "Q3：ΔL*（辅助）"],
    ]
    work = [
        ["质量指标预处理 → 赋权 → 冲突消解", "配比代理比较 → SCI 均值预测 → 风险候选"],
        ["B1 拟合经典骨架 R(N,D)", "构造 ψ_Q^rel(Q,p) × ψ_p(p,N)"],
        ["固定上下文 L_ctx 与预算 C", "枚举 p 和活跃约束，联合求 N、D、Q"],
        ["训练算力前沿分解 + Loss–能力增量桥", "候选预测器比较 + 长期情景外推"],
    ]
    checks = [
        ["A2/A3 扩展余集", "A6–A11 固定检验", "A12–A15 外推讨论"],
        ["B2–B5 跨族验证", "B7 质量外层验证", "γ_p 未识别做敏感性"],
        ["三档预算与连续扫描", "质量成本函数对比", "上下文 L_ctx 敏感性"],
        ["C8 逐任务检验", "C5→C6 外层验证", "3 月 OOF vs Persistence"],
    ]
    outputs = [
        ["领域质量 Q_i", "p_risk、p_safe", "及配比结构证据"],
        ["广义损失函数", "边际效用与替代条件", "外推/识别状态"],
        ["最优配置与 L*(C)", "R0/R1/R2 转移", "等效算力与稳健性"],
        ["贡献分解与预测区间", "12/24 月条件情景", "证据范围说明"],
    ]
    transfer_labels = [
        "Q_res → 17 域 Q_i；配比 p 和结构桥",
        "L(N,D,Q,p) 与参数/外推边界",
        "ΔL*(C₀,C₁) 仅供前沿增量核对",
    ]
    for i, y in enumerate(ys):
        color, light = colors[i], lights[i]
        f.card(x_stage, y, w_stage, 168, fill=color, stroke="none", radius=17)
        f.label(x_stage + 10, y + 36, w_stage - 20, 42, stage_titles[i], 27,
                WHITE, True, align="center")
        f.label(x_stage + 10, y + 91, w_stage - 20, 30, stage_subs[i], 18,
                WHITE, align="center")
        for x, w in [(x_in, w_in), (x_do, w_do), (x_check, w_check), (x_out, w_out)]:
            f.card(x, y, w, 168)
        f.rect(x_in, y, w_in, 43, fill=light, radius=13)
        f.rect(x_do, y, w_do, 43, fill=light, radius=13)
        f.rect(x_check, y, w_check, 43, fill=light, radius=13)
        f.rect(x_out, y, w_out, 43, fill=light, radius=13)
        for x, w, title in [(x_in, w_in, "输入"), (x_do, w_do, "计算/建模"),
                            (x_check, w_check, "校验与边界"), (x_out, w_out, "输出")]:
            f.label(x + 16, y + 5, w - 32, 31, title, 18, color, True)
        f.label(x_in + 17, y + 53, w_in - 34, 101, inputs[i], 16, NAVY, valign="top")
        f.label(x_do + 19, y + 57, w_do - 38, 94, work[i], 17, NAVY, valign="top")
        f.label(x_check + 17, y + 53, w_check - 34, 102, checks[i], 16, NAVY, valign="top")
        f.label(x_out + 17, y + 53, w_out - 34, 102, outputs[i], 16, NAVY, valign="top")
        for a, b in [(x_stage + w_stage, x_in), (x_in + w_in, x_do),
                     (x_do + w_do, x_check), (x_check + w_check, x_out)]:
            f.arrow([(a + 3, y + 92), (b - 8, y + 92)], color=color, width=2.7)
        if i < 3:
            cx = x_stage + w_stage / 2
            f.arrow([(cx, y + 171), (cx, ys[i + 1] - 9)],
                    color=colors[i + 1], width=2.7, dash=(i == 2))
            f.pill(270, y + 179, 585, 34, transfer_labels[i], light,
                   color, size=15)
    f.rect(52, 1038, 1688, 1, fill=LINE)
    f.label(53, 1048, 1685, 34,
            "读图提示：第三问的 p_safe 直接取自第一问；第四问历史前沿以 C 数据为主，Q3 的 ΔL* 为条件性辅助核对。",
            16, MUTED)
    f.save("四问整体流程图")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    technical_route_diagram()
    flow_diagram()
