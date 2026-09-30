# ============ 1.2 指标构造 ============
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy import stats
from sympy import Line2D
from matplotlib.lines import Line2D


from base import C_CORAL, C_GOLD, C_NAVY, C_TEAL, savefig
from dataloader import A1, A2, A3
import networkx as nx

from preprocess_quality_signals import MB_FIELDS




IND_POS = ['fineweb_edu', 'fluency_en', 'modernbert_cleanliness', 'modernbert_readability', 'modernbert_reasoning',
           'modernbert_professionalism', 'dsir_books', 'dsir_wiki', 'dsir_math', 'qurater',
           'rps_doc_unigram_entropy', 'rps_doc_frac_unique_words', 'rps_lines_ending_with_terminal_punctution_mark']
IND_NEG = ['ad_en', 'rps_doc_frac_no_alph_words', 'rps_doc_frac_chars_top_2gram', 'rps_doc_frac_chars_top_3gram',
           'rps_lines_uppercase_letter_fraction', 'rps_lines_numerical_chars_fraction']
IND_INT = ['rps_doc_word_count', 'rps_doc_num_sentences', 'rps_doc_mean_word_length']
INDICATORS = IND_POS + IND_NEG + IND_INT
assert len(INDICATORS) == 22
DIRECTION = {j: '+' for j in IND_POS}; DIRECTION.update({j: '-' for j in IND_NEG}); DIRECTION.update({j: '~' for j in IND_INT})

# 中文短名（用于图表）
SHORT = {'fineweb_edu': '教育价值', 'fluency_en': '流畅度', 'ad_en': '广告概率', 'modernbert_cleanliness': '干净度',
         'modernbert_readability': '可读性', 'modernbert_reasoning': '推理性', 'modernbert_professionalism': '专业性',
         'dsir_books': 'DSIR书籍', 'dsir_wiki': 'DSIR维基', 'dsir_math': 'DSIR数学', 'qurater': 'QuRating',
         'rps_doc_word_count': '词数', 'rps_doc_num_sentences': '句子数', 'rps_doc_unigram_entropy': '一元词熵',
         'rps_doc_frac_unique_words': '独特词占比', 'rps_doc_frac_no_alph_words': '非字母词占比',
         'rps_doc_frac_chars_top_2gram': '高频2gram占比', 'rps_doc_frac_chars_top_3gram': '高频3gram占比',
         'rps_lines_uppercase_letter_fraction': '大写字母占比',
         'rps_lines_ending_with_terminal_punctution_mark': '行末标点占比',
         'rps_lines_numerical_chars_fraction': '数字字符占比', 'rps_doc_mean_word_length': '平均词长'}
MODEL_BASED = ['fineweb_edu', 'fluency_en', 'ad_en'] + MB_FIELDS + ['dsir_books', 'dsir_wiki', 'dsir_math', 'qurater']
RULE_BASED = [j for j in INDICATORS if j not in MODEL_BASED]

# 四个评价维度（用于冲突分析与消解）
DIMS = {'D1 语义价值': ['fineweb_edu', 'qurater', 'modernbert_reasoning', 'modernbert_professionalism', 'dsir_books', 'dsir_wiki', 'dsir_math'],
        'D2 语言表达': ['fluency_en', 'modernbert_readability', 'rps_lines_ending_with_terminal_punctution_mark', 'rps_doc_mean_word_length'],
        'D3 信息结构': ['rps_doc_unigram_entropy', 'rps_doc_frac_unique_words', 'rps_doc_word_count', 'rps_doc_num_sentences'],
        'D4 干净度':   ['modernbert_cleanliness', 'ad_en', 'rps_doc_frac_no_alph_words', 'rps_doc_frac_chars_top_2gram',
                        'rps_doc_frac_chars_top_3gram', 'rps_lines_uppercase_letter_fraction', 'rps_lines_numerical_chars_fraction']}
DIM_OF = {j: d for d, js in DIMS.items() for j in js}
assert sorted(DIM_OF) == sorted(INDICATORS)
DIM_COLORS = dict(zip(DIMS, [C_NAVY, C_TEAL, C_GOLD, C_CORAL]))

# ---- 分类器方向的数据判定 ----
web = A1['domain'].isin(['c4', 'commoncrawl']); acad = A1['domain'].isin(['arxiv', 'wikipedia'])
AD_P1_IS_NONAD = A1.loc[web, 'ad_p1'].mean() < A1.loc[acad, 'ad_p1'].mean()
FL_P1_IS_FLUENT = A1.loc[A1['domain'] == 'arxiv', 'fluency_p1'].mean() > A1.loc[A1['domain'] == 'github', 'fluency_p1'].mean()
print('ad_p1 域均值: 网页域 %.3f vs 学术域 %.3f  =>  第1类为%s' % (A1.loc[web, 'ad_p1'].mean(), A1.loc[acad, 'ad_p1'].mean(), '"非广告"，取 P_ad = 1 - p1' if AD_P1_IS_NONAD else '"广告"，取 P_ad = p1'))
print('fluency_p1 域均值: arxiv %.3f vs github %.3f  =>  第1类为%s' % (A1.loc[A1['domain'] == 'arxiv', 'fluency_p1'].mean(), A1.loc[A1['domain'] == 'github', 'fluency_p1'].mean(), '"流畅"，取 p1' if FL_P1_IS_FLUENT else '"不流畅"，取 1 - p1'))

def build_indicators(df):
    R = pd.DataFrame(index=df.index)
    R['fineweb_edu'] = df['fineweb_edu']
    R['fluency_en'] = df['fluency_p1'] if FL_P1_IS_FLUENT else 1.0 - df['fluency_p1']
    R['ad_en'] = (1.0 - df['ad_p1']) if AD_P1_IS_NONAD else df['ad_p1']
    for c in MB_FIELDS:
        R[c] = df[c]
    R['qurater'] = df[['qurater_1', 'qurater_2', 'qurater_3', 'qurater_4']].mean(axis=1)
    wc = df['rps_doc_word_count'].clip(lower=1)
    for c in ('dsir_books', 'dsir_wiki', 'dsir_math'):
        R[c] = df[c] / wc
    for c in ['rps_doc_word_count', 'rps_doc_num_sentences', 'rps_doc_unigram_entropy', 'rps_doc_frac_unique_words',
              'rps_doc_frac_no_alph_words', 'rps_doc_frac_chars_top_2gram', 'rps_doc_frac_chars_top_3gram',
              'rps_lines_uppercase_letter_fraction', 'rps_lines_ending_with_terminal_punctution_mark',
              'rps_lines_numerical_chars_fraction', 'rps_doc_mean_word_length']:
        R[c] = df[c]
    return R[INDICATORS]

R1, R2, R3 = build_indicators(A1), build_indicators(A2), build_indicators(A3)
print('\nDSIR 原始值 / 每词值 与 lg(词数) 的 Spearman 相关（A1）: %.3f / %.3f' % (
    stats.spearmanr(A1['dsir_books'], np.log1p(A1['rps_doc_word_count']))[0],
    stats.spearmanr(R1['dsir_books'], np.log1p(A1['rps_doc_word_count']))[0]))

desc = pd.DataFrame({'类型': [DIRECTION[j] for j in INDICATORS], '维度': [DIM_OF[j] for j in INDICATORS],
                     '评分器': ['模型' if j in MODEL_BASED else '规则' for j in INDICATORS],
                     'A1均值': R1.mean(), 'A1中位数': R1.median(), 'A1_1%': R1.quantile(0.01), 'A1_99%': R1.quantile(0.99)}, index=INDICATORS)
desc.index = [SHORT[j] + ' (' + j + ')' for j in INDICATORS]
print('\n22 个指标的类型、维度与 A1 分布摘要（+ 正向 / - 负向 / ~ 区间型）:')
#nx.display(desc)



# ============ 1.2 方向统一 + 归一化（阈值一律取自 A1，三集共用） ============
BOUNDS = {j: (float(np.nanpercentile(R1[j], 1)), float(np.nanpercentile(R1[j], 99))) for j in IND_POS + IND_NEG}
INTERVAL = {'rps_doc_word_count': (50.0, 1e5, float(np.nanpercentile(R1['rps_doc_word_count'], 99.9)), True),
            'rps_doc_num_sentences': (3.0, float(np.nanpercentile(R1['rps_doc_num_sentences'], 95)), float(np.nanpercentile(R1['rps_doc_num_sentences'], 99.9)), True),
            'rps_doc_mean_word_length': (3.0, 10.0, float(np.nanpercentile(R1['rps_doc_mean_word_length'], 99.9)), False)}
MEDIAN = R1.median()

def interval_score(v, lo, hi, vmax, use_log):
    v = np.asarray(v, float)
    if use_log:
        t, tlo, thi, tmax = np.log10(1 + np.maximum(v, 0)), np.log10(1 + lo), np.log10(1 + hi), np.log10(1 + vmax)
    else:
        t, tlo, thi, tmax = v, lo, hi, vmax
    s = np.ones_like(t)
    below = t < tlo; s[below] = np.clip(t[below] / tlo, 0, 1)
    above = t > thi; s[above] = np.clip(1 - (t[above] - thi) / max(tmax - thi, 1e-9), 0, 1)
    return s

def normalize(R):
    X = pd.DataFrame(index=R.index)
    for j in INDICATORS:
        v = R[j].fillna(MEDIAN[j]).astype(float)
        if j in INTERVAL:
            lo, hi, vmax, lg = INTERVAL[j]; X[j] = interval_score(v, lo, hi, vmax, lg)
        else:
            lo, hi = BOUNDS[j]; x = ((v.clip(lo, hi) - lo) / (hi - lo)).values
            X[j] = 1 - x if j in IND_NEG else x
    return X

X1, X2, X3 = normalize(R1), normalize(R2), normalize(R3)
print('归一化后取值范围检查: A1 [%.3f, %.3f], A2 [%.3f, %.3f], A3 [%.3f, %.3f]' % (X1.values.min(), X1.values.max(), X2.values.min(), X2.values.max(), X3.values.min(), X3.values.max()))
print('区间型参数:', {k: (round(v[0], 1), round(v[1], 1)) for k, v in INTERVAL.items()})

# ---- 图 1：22 个归一化指标在 7 个域上的经验累积分布（A1） ----
DOMAINS = sorted(A1['domain'].unique())
DOM_PALETTE = ['#1F3A5F', '#2A9D8F', '#E76F51', '#E9C46A', '#6D597A', '#8AB17D', '#B56576']
DOM_COLORS = dict(zip(DOMAINS, DOM_PALETTE[:len(DOMAINS)]))
# 用 ECDF 而非核密度：归一化后很多指标在 0 或 1 处有点质量（截尾 / 区间型），ECDF 能如实显示这些跳跃且不受带宽影响
fig, axes = plt.subplots(4, 6, figsize=(17, 10.5))
grid = np.linspace(0, 1, 201)
for ax, j in zip(axes.ravel(), INDICATORS):
    for d in DOMAINS:
        v = np.sort(X1.loc[A1['domain'] == d, j].values)
        F = np.searchsorted(v, grid, side='right') / len(v)
        ax.plot(grid, F, color=DOM_COLORS[d], lw=1.4, alpha=0.9)
    ax.set_title('%s (%s)' % (SHORT[j], DIRECTION[j]), fontsize=9.5, color=DIM_COLORS[DIM_OF[j]])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02); ax.set_yticks([0, 0.5, 1]); ax.tick_params(labelsize=8)
for ax in axes.ravel()[len(INDICATORS):]:
    ax.axis('off')
handles = [Line2D([0], [0], color=DOM_COLORS[d], lw=2, label=d) for d in DOMAINS]
handles += [Patch(facecolor='none', edgecolor='none', label='   ')] + [Patch(facecolor=DIM_COLORS[d], label=d) for d in DIMS]
fig.legend(handles=handles, loc='lower center', ncol=12, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.01))
fig.suptitle('图 1  方向统一并归一化后 22 个质量指标在 A1 七个域上的经验累积分布 ECDF（标题颜色 = 所属维度；+ 正向 / - 负向 / ~ 区间型）', fontsize=12, y=0.995)
plt.tight_layout(rect=(0, 0.03, 1, 0.98))
plt.savefig('fig01_indicator_distributions.png'); plt.show()