# ============ 1.1 读取 A1 / A2 / A3 全量记录 ============
import time
import pandas as pd

from preprocess_quality_signals import NUM_COLS, RAW_A1, RAW_A2, RAW_A3, load_signals


t0 = time.time()
A1 = load_signals('A1_sample', RAW_A1)
A2 = load_signals('A2_arxiv', RAW_A2, fixed_domain='arxiv')
A3 = load_signals('A3_github', RAW_A3, fixed_domain='github')
A1['set'], A2['set'], A3['set'] = 'A1 抽样集', 'A2 扩展集(arxiv)', 'A3 扩展集(github)'
print('读取耗时 %.1fs' % (time.time() - t0))

print('\nA1 各域记录数:')
print(A1['domain'].value_counts().to_string())

# 缺失率（只看 22 个指标相关列）
miss = pd.DataFrame({'A1': A1[NUM_COLS[:25]].isna().mean(), 'A2': A2[NUM_COLS[:25]].isna().mean(), 'A3': A3[    NUM_COLS[:25]].isna().mean()})
miss = miss[(miss > 0).any(axis=1)]
print('\n存在缺失的字段及缺失率（其余字段无缺失）:')
print((miss * 100).round(3).to_string() if len(miss) else '  无缺失')