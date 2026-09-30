# -*- coding: utf-8 -*-
"""
C8 逐任务评测 JSON 的本地聚合脚本（仅用标准库，Python 3.8+ 均可运行）。
放在 real_attachments/C_efficiency_evolution/ 下运行，读取 ./detailed_results/<model_dir>/results_*.json，
每个模型目录只取"时间戳最新且可解析"的一份 JSON（数据说明：4 个 JSON 被截断，宜按目录取最新可解析记录）。
输出（./c8_cache/）：
  c8_task_scores_wide.csv.xz  每行一个模型；列 = 任务|指标（acc / acc_norm / exact_match / prompt_level_strict_acc ...）
                              及其 stderr（后缀 _se）与有效样本数（后缀 |n）
  c8_meta.csv                 模型名、参数量、评测日期、耗时、所用 JSON 文件、解析状态
  c8_task_config.json         各任务的 n-shot、higher_is_better、样本数（取自第一份成功解析的 JSON）
  c8_parse_log.txt            解析日志（含截断/失败文件清单）
"""
import os, sys, json, csv, lzma, time, re, io

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'detailed_results')
OUT = os.path.join(ROOT, 'c8_cache')
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, 'c8_parse_log.txt'), 'w', encoding='utf-8')
def log(s):
    print(s); LOG.write(s + '\n'); LOG.flush()

METRICS = ['acc', 'acc_norm', 'exact_match', 'prompt_level_strict_acc', 'inst_level_strict_acc', 'prompt_level_loose_acc', 'inst_level_loose_acc']

def ts_of(fname):
    m = re.search(r'results_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:\.\d+)?)', fname)
    return m.group(1) if m else fname

def try_load(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return None, '%s: %s' % (type(e).__name__, str(e)[:120])

t0 = time.time()
dirs = sorted(d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d)))
log('模型目录数: %d' % len(dirs))
rows, meta, task_cfg = [], [], None
all_cols = set()
n_trunc, n_fail = 0, 0
for i, d in enumerate(dirs):
    files = sorted([f for f in os.listdir(os.path.join(SRC, d)) if f.endswith('.json')], key=ts_of, reverse=True)
    data, used, errs = None, None, []
    for f in files:
        data, err = try_load(os.path.join(SRC, d, f))
        if data is not None and 'results' in data:
            used = f; break
        errs.append('%s -> %s' % (f, err)); n_trunc += 1
    if data is None:
        n_fail += 1; log('[FAIL] %s: 无可解析 JSON (%s)' % (d, '; '.join(errs))); meta.append({'model_dir': d, 'status': 'fail', 'json_file': '', 'n_json_files': len(files), 'skipped_files': '; '.join(errs)}); continue
    if errs: log('[SKIP] %s: 跳过截断文件 %s，改用 %s' % (d, '; '.join(errs), used))
    cfg = data.get('config', {}) or {}
    ns = data.get('n-samples', {}) or {}
    row = {'model_dir': d}
    for task, res in (data.get('results') or {}).items():
        for k, v in res.items():
            if k == 'alias': continue
            name, _, filt = k.partition(',')
            if name.endswith('_stderr'):
                base = name[:-7]
                if base in METRICS and isinstance(v, (int, float)): row['%s|%s_se' % (task, base)] = v
            elif name in METRICS and isinstance(v, (int, float)):
                row['%s|%s' % (task, name)] = v
        if task in ns and isinstance(ns[task], dict):
            row['%s|n' % task] = ns[task].get('effective', ns[task].get('original'))
    all_cols.update(row.keys()); rows.append(row)
    meta.append({'model_dir': d, 'status': 'ok', 'json_file': used, 'n_json_files': len(files), 'skipped_files': '; '.join(errs),
                 'model_name': data.get('model_name', ''), 'model_num_parameters': cfg.get('model_num_parameters', ''), 'model_dtype': cfg.get('model_dtype', ''),
                 'date_unix': data.get('date', ''), 'start_time': data.get('start_time', ''), 'end_time': data.get('end_time', ''),
                 'total_evaluation_time_seconds': data.get('total_evaluation_time_seconds', ''), 'transformers_version': data.get('transformers_version', ''), 'model_sha': cfg.get('model_sha', '')})
    if task_cfg is None:
        task_cfg = {'n_shot': data.get('n-shot', {}), 'higher_is_better': data.get('higher_is_better', {}), 'n_samples': ns, 'group_subtasks': data.get('group_subtasks', {}), 'versions': data.get('versions', {})}
    if (i + 1) % 200 == 0: log('  已处理 %d / %d，耗时 %.0fs' % (i + 1, len(dirs), time.time() - t0))

cols = ['model_dir'] + sorted(c for c in all_cols if c != 'model_dir')
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols); w.writeheader()
for r in rows: w.writerow({c: r.get(c, '') for c in cols})
with lzma.open(os.path.join(OUT, 'c8_task_scores_wide.csv.xz'), 'wt', encoding='utf-8') as f: f.write(buf.getvalue())
mcols = ['model_dir', 'status', 'json_file', 'n_json_files', 'skipped_files', 'model_name', 'model_num_parameters', 'model_dtype', 'date_unix', 'start_time', 'end_time', 'total_evaluation_time_seconds', 'transformers_version', 'model_sha']
with open(os.path.join(OUT, 'c8_meta.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=mcols); w.writeheader()
    for m in meta: w.writerow({c: m.get(c, '') for c in mcols})
with open(os.path.join(OUT, 'c8_task_config.json'), 'w', encoding='utf-8') as f: json.dump(task_cfg, f, ensure_ascii=False, indent=1)
log('完成: 成功 %d 个模型, 失败 %d 个, 跳过截断/损坏文件 %d 个, 列数 %d, 耗时 %.0fs' % (len(rows), n_fail, n_trunc, len(cols), time.time() - t0))
LOG.close()
