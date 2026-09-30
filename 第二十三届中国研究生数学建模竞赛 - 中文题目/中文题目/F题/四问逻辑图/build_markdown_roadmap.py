"""Generate the editable, continuous Markdown argument roadmap."""

from pathlib import Path
from wcwidth import wcswidth


OUT = Path(__file__).with_name("四问核心论证链.md")
WIDTH = 94
BRANCH_WIDTH = 44
GAP = 6
LEFT_CENTER = BRANCH_WIDTH // 2
RIGHT_CENTER = BRANCH_WIDTH + GAP + BRANCH_WIDTH // 2
CENTER = WIDTH // 2
lines = []


def fit(s, n):
    width = wcswidth(s)
    if width > n:
        raise ValueError(f"Text exceeds {n} columns ({width}): {s}")
    return s + " " * (n - width)


def box(content, width=WIDTH, double=False):
    tl, tr, vl, bl, br, hor = (
        ("╔", "╗", "║", "╚", "╝", "═")
        if double else ("┌", "┐", "│", "└", "┘", "─")
    )
    rows = [tl + hor * (width - 2) + tr]
    rows += [vl + " " + fit(s, width - 4) + " " + vl for s in content]
    rows.append(bl + hor * (width - 2) + br)
    return rows


def point_line(items):
    chars = [" "] * WIDTH
    for pos, char in items:
        chars[pos] = char
    return "".join(chars).rstrip()


def split():
    lines.append(point_line([(CENTER, "│")]))
    chars = [" "] * WIDTH
    chars[LEFT_CENTER], chars[CENTER], chars[RIGHT_CENTER] = "┌", "┴", "┐"
    for x in range(LEFT_CENTER + 1, RIGHT_CENTER):
        if x != CENTER:
            chars[x] = "─"
    lines.append("".join(chars).rstrip())
    lines.append(point_line([(LEFT_CENTER, "▼"), (RIGHT_CENTER, "▼")]))


def pair(left, right):
    a, b = box(left, BRANCH_WIDTH), box(right, BRANCH_WIDTH)
    if len(a) != len(b):
        raise ValueError("Branch heights differ")
    lines.extend(x + " " * GAP + y for x, y in zip(a, b))


def merge():
    lines.append(point_line([(LEFT_CENTER, "│"), (RIGHT_CENTER, "│")]))
    chars = [" "] * WIDTH
    chars[LEFT_CENTER], chars[CENTER], chars[RIGHT_CENTER] = "└", "┬", "┘"
    for x in range(LEFT_CENTER + 1, RIGHT_CENTER):
        if x != CENTER:
            chars[x] = "─"
    lines.append("".join(chars).rstrip())
    lines.append(point_line([(CENTER, "▼")]))


def handoff(label, conditional=False):
    lines.append(point_line([(CENTER, "┊" if conditional else "│")]))
    text_width = wcswidth(label)
    if text_width > WIDTH:
        raise ValueError(f"Handoff exceeds {WIDTH} columns: {label}")
    lines.append(" " * ((WIDTH - text_width) // 2) + label)
    lines.append(point_line([(CENTER, "⇣" if conditional else "▼")]))


lines += box(["F 题四问：质量与配比 → 广义损失 → 预算最优 → 历史能力前沿"], double=True)
handoff("从数据证据进入问题一")

lines += box(["问题一｜A1–A3 质量记录＋A4/A5 配比实验"])
split()
pair(
    ["质量分支：A1–A3", "22 指标 → Q_lin", "冲突几何消解 → Q_res", "A16 映射 → 17 域 Q_i"],
    ["配比分支：A4/A5", "SCM → SCI 均值预测", "MPR-MTL → 风险 p_risk", "凸包保守 p_safe；对数系数/p_ref"],
)
merge()
lines += box([
    "Q1 输出：Q_i、p_risk、p_safe、对数系数/p_ref",
    "创新①：非完全补偿的 Q_res＋稳定筛选的 SCI",
    "验证：A6–A11 跨规模排序；质量有效份额 η＝0",
], double=True)
handoff("Q_i、p_risk、对数配比桥 → Q2；p_safe 另直达 Q3")

lines += box(["问题二｜接收 Q1 的 Q、p 和对数桥，另引入 B 组证据"])
split()
pair(
    ["规模分支：B1–B5", "B1 → R(N,D)", "B2–B5 → 轨迹与跨族验证"],
    ["质量与配比分支：B6/B7＋Q1", "Q_i、p → Q_0(p) → ψ_Q^rel", "对数桥 → ψ_p；γ_p 未识别"],
)
merge()
lines += box([
    "Q2 输出：L(N,D,Q,p)＝E＋R(N,D)·ψ_Q^rel·ψ_p",
    "创新②：相对质量因子在 Q_0(p) 处等于 1，避免重复计入",
    "边界：SCI 未进入 Q2 主公式；γ_p 名义取 0",
], double=True)
handoff("广义损失 L、Q_0(p) 与参数边界 → Q3")

lines += box(["问题三｜接收 Q2 的广义损失，另取 Q1 的可执行配比候选"])
split()
pair(
    ["目标与候选", "Q2 → L(N,D,Q,p)", "Q1 → p_risk/p_safe/p_measured", "p_ref 仅作参考"],
    ["预算与约束", "C7 → 外生上下文", "训练＋注意力＋质量治理成本", "活跃集求 N、D、Q"],
)
merge()
lines += box([
    "Q3 输出：(N*,D*,Q*,p*) 与 L*(C)",
    "创新③：有限候选联立寻优＋R0/R1/R2 结构转移",
    "边界：高预算属于远距离外推",
], double=True)
handoff("ΔL*(C₀,C₁) ⇢ 仅作 Q4 的条件性辅助核对", conditional=True)

lines += box(["问题四｜C 组历史能力证据为主，Q3 的损失增量为旁证"])
split()
pair(
    ["历史能力主通道", "C1/C8 → 综合能力 S", "C1×C4 → Compute-Q90", "归因：算力/时间漂移/残差"],
    ["桥接与预测通道", "C5→C6 → 桥接外层验证", "Q3 ΔL* ⇢ 锚定增量核对", "3 月回测 → 12/24 月情景"],
)
merge()
lines += box([
    "Q4 输出：能力归因与 12/24 个月前沿情景",
    "创新④：训练算力归因＋桥接外验＋锚定增量",
    "边界：长期预测没有直接样本外回测",
], double=True)

content = "# F 题四问一体化论证路线图\n\n```text\n" + "\n".join(lines) + "\n```\n\n"
content += (
    "**箭头含义：**`▼` 表示正式传递，`⇣` 和 `⇢` 表示条件性辅助核对。"
    "SCI 是第一问的均值预测器；第二问使用第一问旧版输出的对数混料模型构造可解析配比桥。\n\n"
)
content += (
    "**代码接口提示：**第二问的匹配配比复核仍回读原始 A6–A9；"
    "题目要求附件 A 的信息通过第一问输出进入第二问。\n"
)
OUT.write_text(content, encoding="utf-8")
print(OUT)
print(f"Diagram lines: {len(lines)}; maximum width: {max(wcswidth(s) for s in lines)}")
