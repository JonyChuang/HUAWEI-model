# ============ 0. 环境配置（只需运行一次） ============
import os, sys, json, lzma, glob, math, time, warnings, itertools, csv
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
import seaborn as sns
from scipy import stats
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression, Ridge, RidgeCV
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import KFold

warnings.filterwarnings('ignore')
import logging
logging.getLogger('matplotlib').setLevel(logging.ERROR)          # 屏蔽 "does not have a glyph" 等字体日志
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
pd.set_option('display.width', 180)
pd.set_option('display.max_columns', 40)
pd.set_option('display.float_format', lambda v: '%.4f' % v)

# ---- 中文字体（Windows 默认字体） ----
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Noto Sans CJK SC', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 110
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.color'] = '#E4E4E4'
plt.rcParams['grid.linewidth'] = 0.6
plt.rcParams['axes.edgecolor'] = '#555555'
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['font.size'] = 10

# ---- 统一配色（深蓝 / 青绿 / 珊瑚 / 金 / 紫灰） ----
C_NAVY, C_TEAL, C_CORAL, C_GOLD, C_PLUM, C_GREY = '#1F3A5F', '#2A9D8F', '#E76F51', '#E9C46A', '#6D597A', '#9E9E9E'
PALETTE = [C_NAVY, C_TEAL, C_CORAL, C_GOLD, C_PLUM, '#8AB17D', '#264653', '#B56576']
CMAP_DIV = sns.diverging_palette(230, 20, as_cmap=True)          # 蓝 - 白 - 红
CMAP_SEQ = sns.light_palette(C_NAVY, as_cmap=True)
CMAP_TC  = mpl.colors.LinearSegmentedColormap.from_list('tc', [C_TEAL, C_GOLD, C_CORAL])
RNG = np.random.default_rng(2026)

# ---- 路径 ----
#BASE_DIR = Path('.').resolve()
# __file__ 是当前脚本的路径，parent 是 "代码" 文件夹，parent.parent 就是 "F题" 文件夹
BASE_DIR = Path(__file__).resolve().parent.parent
def find_data_root():
    for c in [BASE_DIR / 'real_attachments' / 'A_data_value', BASE_DIR / 'A_data_value', BASE_DIR]:
        if (c / 'regmix_tables').is_dir():
            return c
    raise FileNotFoundError('未找到 A_data_value 目录，请把 notebook 放在 real_attachments 的上一级目录（F题/）下')
DATA = find_data_root()
REG = DATA / 'regmix_tables'
CACHE = DATA / 'signals_cache'
OUT = BASE_DIR / 'output_q1'; FIG = OUT / 'figures'; TAB = OUT / 'tables'
for d in (FIG, TAB, CACHE):
    d.mkdir(parents=True, exist_ok=True)

def savefig(name):
    plt.savefig(FIG / name, dpi=300, bbox_inches='tight')

print('数据目录:', DATA)
print('输出目录:', OUT)