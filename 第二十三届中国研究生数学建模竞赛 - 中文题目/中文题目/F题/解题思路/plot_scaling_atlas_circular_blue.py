"""Circular aperture for the notebook's existing Cartesian log-log scaling law.

Only the presentation frame changes. The model, observed coordinates, optimal
functions, compute geometry, and numerical annotations are reused unchanged.
"""

from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from matplotlib import patheffects


HERE = Path(__file__).resolve().parent
TITLE = "计算约束下的标度律损失地形与最优资源轨迹"
BG = "#FCFCFA"
INK = "#252525"
NAVY = "#123A63"
TEAL = "#2A9D8F"
PLUM = "#E4B4AA"
CORAL = "#D98B7D"
GOLD = "#D6A33A"
GUIDE = "#E9EEF2"
FRAME = "#324A5F"
CX, CY, RADIUS = 0.85, 2.20, 2.75  # Cartesian log10(N/B), log10(D/B)
DIAMETER_IN = 5.10


def _fonts():
    paths = [
        HERE / 'fonts' / 'FandolSong-Regular.otf',
        HERE / 'fonts' / 'FandolSong-Bold.otf',
        Path('C:/Windows/Fonts/times.ttf'),
        Path('C:/Windows/Fonts/timesi.ttf'),
        Path('C:/Windows/Fonts/timesbd.ttf'),
    ]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Required figure font missing: {path}")
        font_manager.fontManager.addfont(str(path))
    mpl.rcParams.update({
        "font.family": ["Times New Roman", "FandolSong"],
        "mathtext.fontset": "custom",
        "mathtext.rm": "Times New Roman",
        "mathtext.it": "Times New Roman:italic",
        "mathtext.bf": "Times New Roman:bold",
        "mathtext.cal": "Times New Roman",
        "mathtext.sf": "Times New Roman",
        "mathtext.tt": "Times New Roman",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "figure.facecolor": BG,
        "savefig.facecolor": BG,
        "axes.facecolor": BG,
        "text.color": INK,
        "font.size": 7.7,
    })
    return font_manager.FontProperties(fname=str(paths[-1]))


def _logb(series):
    values = np.asarray(series, dtype=float)
    assert np.isfinite(values).all() and (values > 0).all()
    return np.log10(values)


def _clip(artist, circle):
    artist.set_clip_path(circle)
    return artist


def _ring(ax):
    theta = np.linspace(0, 2 * np.pi, 721)
    xx = CX + RADIUS * np.cos(theta)
    yy = CY + RADIUS * np.sin(theta)
    # Short vector paths keep the boundary precise and collision-auditable.
    for start in range(0, len(theta) - 1, 20):
        stop = min(start + 21, len(theta))
        ax.plot(xx[start:stop], yy[start:stop], color=FRAME, lw=0.98, alpha=.88,
                solid_capstyle="round", zorder=15, clip_on=False)


def _edge_ticks(ax):
    data_per_pt = (2 * RADIUS) / (DIAMETER_IN * 72)
    major_len = 4.5 * data_per_pt
    minor_len = 2.25 * data_per_pt
    offset = 13 * data_per_pt

    x_major = [(-1, "0.1"), (0, "1"), (1, "10"), (2, "100"), (3, "1,000")]
    y_major = [(0, "1"), (1, "10"), (2, "100"), (3, "1,000"), (4, "10,000")]
    x_minor = [np.log10(m * 10 ** k) for k in range(-2, 4) for m in (2, 5)]
    y_minor = [np.log10(m * 10 ** k) for k in range(-1, 5) for m in (2, 5)]

    def x_tick(x, length, label=None):
        dx = x - CX
        if abs(dx) >= RADIUS:
            return
        y = CY - np.sqrt(RADIUS ** 2 - dx ** 2)
        ux, uy = (CX - x) / RADIUS, (CY - y) / RADIUS
        ax.plot([x, x + ux * length], [y, y + uy * length],
                color=FRAME, lw=0.75 if label else 0.5, zorder=16, clip_on=False)
        if label:
            ax.text(x - ux * offset, y - uy * offset, label, fontsize=7.2,
                    ha="center", va="top", clip_on=False, zorder=17)

    def y_tick(y, length, label=None):
        dy = y - CY
        if abs(dy) >= RADIUS:
            return
        x = CX - np.sqrt(RADIUS ** 2 - dy ** 2)
        ux, uy = (CX - x) / RADIUS, (CY - y) / RADIUS
        ax.plot([x, x + ux * length], [y, y + uy * length],
                color=FRAME, lw=0.75 if label else 0.5, zorder=16, clip_on=False)
        if label:
            ax.text(x - 46 * data_per_pt, y, label, fontsize=7.2,
                    ha="right", va="center", clip_on=False, zorder=17)

    for value in x_minor:
        x_tick(value, minor_len)
    for value in y_minor:
        y_tick(value, minor_len)
    for value, label in x_major:
        x_tick(value, major_len, label)
    for value, label in y_major:
        y_tick(value, major_len, label)


def _compute_guides(ax, circle):
    for power in (19, 22, 24):
        # C=6ND; N and D are in billions, hence the 10^18 factor.
        intercept = power - np.log10(6) - 18
        aa, bb, cc = 2, -2 * CX - 2 * (intercept - CY), CX ** 2 + (intercept - CY) ** 2 - RADIUS ** 2
        roots = np.sort(np.roots([aa, bb, cc]).real)
        x = np.linspace(roots[0], roots[1], 221)
        y = intercept - x
        for start in range(0, len(x) - 1, 20):
            stop = min(start + 21, len(x))
            _clip(ax.plot(x[start:stop], y[start:stop], color=GUIDE, lw=0.88,
                          ls=(0, (2.0, 2.5)), alpha=0.71, zorder=3)[0], circle)
    # The three attached milestone tags identify the compute guides directly.


def _mini_key(fig):
    x0, x1, xt = .847, .884, .895
    rows = [.785, .731, .677, .623, .569]
    fig.add_artist(Line2D([x0, x1], [rows[0], rows[0]], transform=fig.transFigure,
                          color=GOLD, lw=2.65, marker="o", markersize=3.2,
                          markevery=[1], solid_capstyle="round"))
    fig.add_artist(Line2D([x0, x1], [rows[1], rows[1]], transform=fig.transFigure,
                          color=GUIDE, lw=.95, ls=(0, (2, 2.5))))
    fig.text((x0+x1)/2, rows[2], "◇", color=CORAL, fontsize=11, ha="center", va="center")
    fig.text((x0+x1)/2, rows[3], "△", color=PLUM, fontsize=11, ha="center", va="center")
    fig.add_artist(Line2D([(x0+x1)/2], [rows[4]], transform=fig.transFigure,
                          marker="s", markersize=5.1, markerfacecolor="#F0F4F7",
                          markeredgecolor="#274C67", markeredgewidth=.8, linestyle="none"))
    for y, label in zip(rows, ["最优轨迹", "等算力线", "B4 跨族", "B5 文献", "B1 Pythia"]):
        fig.text(xt, y, label, fontsize=7.1, ha="left", va="center", color=INK)
    fig.add_artist(Rectangle((x0, .504), x1-x0, .021,
                             transform=fig.transFigure, facecolor="#52718B",
                             edgecolor="none"))
    fig.add_artist(Line2D([x0+.004, x1-.004], [.514,.514],
                          transform=fig.transFigure, color="#F5F7F8", lw=.9))
    fig.text(xt, .514, "等损失线", fontsize=7.1, ha="left", va="center", color=INK)


def render_atlas(Ng, Dg, L_classic, TH, N_opt, D_opt, B1, B4, B5, output_dir):
    """Render a circle in log-Cartesian coordinates; never transform to polar."""
    _fonts()
    Ng, Dg = np.asarray(Ng, float), np.asarray(Dg, float)
    assert np.all(np.diff(Ng) > 0) and np.all(np.diff(Dg) > 0)
    assert len(B1) == 1176 and len(B4) == 57 and len(B5) == 44
    b1_end = B1.loc[B1.groupby("N_params_B")["D_tokens_B"].idxmax()].sort_values("N_params_B")
    assert len(b1_end) == 8

    # A circular aperture cannot retain the notebook's rectangular corners.
    # The display disk covers every original B1/B4/B5 coordinate, including
    # B4's 33,739B-token point beyond the original Dg upper bound. Only the
    # original fitted function is evaluated on the extended display grid.
    for df in (b1_end, B4, B5):
        radius = np.hypot(_logb(df.N_params_B) - CX, _logb(df.D_tokens_B) - CY)
        assert np.max(radius) < RADIUS - 0.08, "Observed model position would be clipped"

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / TITLE
    fig = plt.figure(figsize=(7.20, 6.40), facecolor=BG)
    ax = fig.add_axes([0.34 / 7.20, 0.74 / 6.40, DIAMETER_IN / 7.20, DIAMETER_IN / 6.40])
    ax.set_xlim(CX - RADIUS, CX + RADIUS)
    ax.set_ylim(CY - RADIUS, CY + RADIUS)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    circle = Circle((CX, CY), RADIUS, transform=ax.transData)

    xg = np.linspace(CX - RADIUS, CX + RADIUS, 820)
    yg = np.linspace(CY - RADIUS, CY + RADIUS, 820)
    XX, YY = np.meshgrid(xg, yg)
    LL = L_classic(10 ** XX * 1e9, 10 ** YY * 1e9, TH)
    assert np.isfinite(LL).all()
    cmap = LinearSegmentedColormap.from_list(
        "scientific_blue_to_warm_loss",
        [(0.00, "#123A63"), (0.24, "#1F5E9C"), (0.49, "#3F82C4"),
         (0.72, "#7FB3D5"), (0.88, "#C8DDEA"), (0.965, "#EEE7D7"),
         (1.00, "#D8B291")], N=256)
    norm = Normalize(vmin=1.80, vmax=3.67, clip=True)
    field = ax.contourf(XX, YY, LL, levels=np.linspace(1.80, 3.67, 56),
                        cmap=cmap, norm=norm, extend="max", antialiased=False,
                        zorder=0)
    field.set_rasterized(True)
    _clip(field, circle)

    # Eight original numerical levels; high-loss annotations are locally
    # knocked out only for typography, leaving the loss field continuous.
    # A small typographic knockout lets the low-compute callout sit on the
    # landscape without a contour running through its glyphs. The model field
    # and all computed contour levels remain unchanged.
    label_gap = (((XX > 0.02) & (XX < 0.79) & (YY > 0.23) & (YY < 0.84)) |
                 ((XX > 1.16) & (XX < 1.84) & (YY > 4.24) & (YY < 4.81)))
    contour_field = np.ma.masked_where(label_gap, LL)
    levels = [1.9, 2.0, 2.1, 2.2, 2.4, 2.6, 2.8, 3.0]
    cs = ax.contour(XX, YY, contour_field, levels=levels, colors="#F5F7F8",
                    linewidths=.82, alpha=.86, zorder=2, corner_mask=False)
    _clip(cs, circle)
    def contour_y(level, x):
        remaining = level - TH["E"] - TH["A"] * (1e9 * 10 ** x) ** (-TH["alpha"])
        return np.log10((TH["B"] / remaining) ** (1 / TH["beta"]) / 1e9)
    label_x = [3.10, 3.00, 2.72, 3.03, 2.44, 1.96, 1.55, .95]
    manual_labels = [(x, contour_y(level, x)) for level, x in zip(levels, label_x)]
    labels = ax.clabel(cs, levels=levels, manual=manual_labels, inline=True,
                       fmt=lambda value: f"{value:.2f}", fontsize=7.1,
                       colors="#F9FBFC")
    for label in labels:
        _clip(label, circle)
        label.set_path_effects([patheffects.withStroke(linewidth=1.1,
                                                       foreground="#1B4263", alpha=.65)])

    cax = fig.add_axes([.780, .315, .016, .48])
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax,
                      ticks=[1.8, 2.2, 2.6, 3.0, 3.4, 3.6])
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2, width=.55, labelsize=7.1, colors="#3F4B55", pad=3)
    cjk = font_manager.FontProperties(
        fname=str(HERE / 'fonts' / 'FandolSong-Regular.otf'))
    fig.text(.767, .817, "预测损失", fontproperties=cjk, fontsize=7.3,
             ha="center", va="bottom", color=INK)

    _compute_guides(ax, circle)
    Cs = np.geomspace(1e17, 1e27, 501)
    xo, yo = _logb(N_opt(Cs) / 1e9), _logb(D_opt(Cs) / 1e9)
    for start in range(0, len(Cs) - 1, 20):
        stop = min(start + 21, len(Cs))
        _clip(ax.plot(xo[start:stop], yo[start:stop], color=GOLD, lw=2.65,
                      solid_capstyle="round", zorder=6)[0], circle)

    marker_spec = [
        (b1_end, "s", 28, "#F0F4F7", "#274C67", .85, 5),
        (B4, "D", 23, "none", CORAL, .85, 5),
        (B5, "^", 25, "none", PLUM, .85, 5),
    ]
    for df, marker, size, face, edge, width, layer in marker_spec:
        marks = ax.scatter(_logb(df.N_params_B), _logb(df.D_tokens_B), marker=marker,
                           s=size, facecolors=face, edgecolors=edge,
                           linewidths=width, alpha=.77, zorder=layer)
        _clip(marks, circle)

    # Three and only three compute-optimal operating points.
    milestone_specs = [
        (1e19, (0.10, 0.55), "left", "center"),
        (1e22, (2.20, 3.72), "left", "center"),
        (1e24, (1.20, 4.54), "left", "center"),
    ]
    for C, text_xy, ha, va in milestone_specs:
        n, d = float(N_opt(C) / 1e9), float(D_opt(C) / 1e9)
        x, y = np.log10(n), np.log10(d)
        loss = float(L_classic(n * 1e9, d * 1e9, TH))
        _clip(ax.scatter([x], [y], s=52, marker="o", facecolors="#F0B83E",
                         edgecolors="#FFF8E7", linewidths=.80, zorder=9), circle)
        if C == 1e19:
            label = (rf"$10^{{19}}$ FLOPs" + "\n"
                     + rf"$N^*={n:.3f}$B" + "\n"
                     + rf"$D^*={d:.2f}$B" + "\n"
                     + rf"$L^*={loss:.3f}$")
        elif C == 1e22:
            label = (rf"$10^{{22}}$ FLOPs" + "\n"
                     + rf"$N^*={n:.2f}$B" + "\n"
                     + rf"$D^*={d:.0f}$B" + "\n"
                     + rf"$L^*={loss:.3f}$")
        else:
            label = (rf"$10^{{24}}$ FLOPs" + "\n"
                     + rf"$N^*={n:.1f}$B" + "\n"
                     + rf"$D^*={d/1000:.2f}$T" + "\n"
                     + rf"$L^*={loss:.3f}$")
        ax.annotate(label, (x, y), xytext=text_xy, textcoords="data",
                    fontsize=7.3, color="#FFFFFF", ha=ha, va=va,
                    linespacing=1.18,
                    bbox=dict(boxstyle="round,pad=0.24,rounding_size=0.07",
                              facecolor="#163A5A", edgecolor="none", alpha=.94),
                    arrowprops=dict(arrowstyle="-", color="#E5B13C", lw=1.1,
                                    shrinkA=5, shrinkB=4), zorder=10)

    _ring(ax)
    _edge_ticks(ax)

    fig.text(0.402, 0.052, "参数量 N（十亿；对数刻度）", fontsize=8.7,
             ha="center", va="center")
    fig.text(0.020, 0.073, "训练 token 数 D\n（十亿；对数刻度）", fontsize=8.4,
             ha="left", va="bottom", linespacing=1.18)
    _mini_key(fig)

    # The colorbar is auxiliary; the circular map is the only data panel.
    sys.path.insert(0, str(HERE))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    require_matplotlib_panel_alignment(fig, axes=[ax], panel_ids=["a"],
                                       json_out=stem.with_suffix(".alignment.json"),
                                       tolerance_pt=1.5, strict=True)
    fig.savefig(stem.with_suffix(".pdf"), dpi=600, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(stem.with_suffix(".svg"), dpi=600, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight", pad_inches=0.08)
    return fig, stem


if __name__ == "__main__":
    TH = pd.read_csv(HERE / "output_q2/tables/classic_law_params.csv", index_col=0).iloc[:, 0].to_dict()
    data = HERE.parent / 'real_attachments' / 'B_scaling_laws'
    B1 = pd.read_csv(data / "pythia_training_log_existing.csv")
    B4 = pd.read_csv(data / "scaling_baseline.csv")
    B5 = pd.read_csv(data / "published_scaling_data.csv")
    def L_classic(N, D, th):
        return th["E"] + th["A"] * np.asarray(N, float) ** (-th["alpha"]) + th["B"] * np.asarray(D, float) ** (-th["beta"])
    exponent = TH["beta"] / (TH["alpha"] + TH["beta"])
    constant = (TH["alpha"] * TH["A"] / (TH["beta"] * TH["B"])) ** (1 / (TH["alpha"] + TH["beta"]))
    def N_opt(C): return constant * (np.asarray(C, float) / 6) ** exponent
    def D_opt(C): return (np.asarray(C, float) / 6) / N_opt(C)
    fig, stem = render_atlas(np.logspace(7, 12.3, 260), np.logspace(8.5, 13.3, 260),
                             L_classic, TH, N_opt, D_opt, B1, B4, B5,
                             HERE / "output_q2/figures")
    print(stem)
    plt.close(fig)
