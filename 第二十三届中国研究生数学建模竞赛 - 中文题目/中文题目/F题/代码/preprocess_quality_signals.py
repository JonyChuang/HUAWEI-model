
import csv
import lzma
import math
import time

from envs.myagent.Lib import json
import pandas as pd

from base import DATA, CACHE, OUT, REG


# ============ 1.1 流式读取器（与 preprocess_quality_signals.py 相同的规则） ============
SCALAR_FIELDS = ['dsir_books', 'dsir_wiki', 'dsir_math',
                 'rps_doc_word_count', 'rps_doc_num_sentences', 'rps_doc_unigram_entropy',
                 'rps_doc_frac_unique_words', 'rps_doc_frac_no_alph_words',
                 'rps_doc_frac_chars_top_2gram', 'rps_doc_frac_chars_top_3gram',
                 'rps_lines_uppercase_letter_fraction', 'rps_lines_ending_with_terminal_punctution_mark',
                 'rps_lines_numerical_chars_fraction', 'rps_doc_mean_word_length']
MB_FIELDS = ['modernbert_cleanliness', 'modernbert_readability', 'modernbert_reasoning', 'modernbert_professionalism']
OUT_COLS = (['id', 'sub_path', 'domain'] + SCALAR_FIELDS +
            ['fineweb_edu', 'fluency_p1', 'ad_p1'] + MB_FIELDS +
            ['qurater_1', 'qurater_2', 'qurater_3', 'qurater_4',
             'n_chars', 'n_lines', 'n_url', 'frac_nonascii', 'snippet'])
NUM_COLS = [c for c in OUT_COLS if c not in ('id', 'sub_path', 'domain', 'snippet')]
CHUNK = 25000

def softmax(z):
    m = max(z); e = [math.exp(v - m) for v in z]; s = sum(e)
    return [v / s for v in e]

def to_float(v, fmt='%.6g'):
    if v is None: return ''
    if isinstance(v, (list, tuple)):
        if len(v) != 1: return ''
        v = v[0]
    try:
        f = float(v)
        return '' if f != f else fmt % f
    except Exception:
        return ''

def compress_record(obj, domain):
    row = {'id': obj.get('id', ''), 'sub_path': obj.get('sub_path', ''), 'domain': domain}
    for c in SCALAR_FIELDS:
        row[c] = to_float(obj.get(c))
    row['fineweb_edu'] = to_float(obj.get('fineweb_edu'))
    for src, dst in (('fluency_en', 'fluency_p1'), ('ad_en', 'ad_p1')):
        v = obj.get(src)
        row[dst] = ('%.6g' % softmax(v)[1]) if isinstance(v, (list, tuple)) and len(v) == 2 else to_float(v)
    for c in MB_FIELDS:
        v = obj.get(c)
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            p = softmax(v); row[c] = '%.6g' % sum(k * pk for k, pk in enumerate(p))
        else:
            row[c] = to_float(v)
    v = obj.get('qurater')
    for k in range(4):
        row['qurater_%d' % (k + 1)] = to_float(v[k]) if isinstance(v, (list, tuple)) and k < len(v) else ''
    text = obj.get('content') or obj.get('text') or ''
    if text:
        n = len(text)
        row['n_chars'] = n; row['n_lines'] = text.count('\n') + 1
        row['n_url'] = text.count('http://') + text.count('https://') + text.count('www.')
        row['frac_nonascii'] = '%.4g' % (sum(1 for ch in text if ord(ch) > 127) / n)
        row['snippet'] = text[:200].replace('\r', ' ').replace('\n', ' ')
    else:
        row['n_chars'] = row['n_lines'] = row['n_url'] = row['frac_nonascii'] = row['snippet'] = ''
    return row

def norm_domain(s):
    s = str(s or 'unknown').lower().replace('redpajama', '').replace('_', '').replace('-', '').strip()
    return {'cc': 'commoncrawl', 'books': 'book', 'wiki': 'wikipedia'}.get(s, s)

def open_any(p):
    p = str(p)
    return lzma.open(p, 'rt', encoding='utf-8') if p.endswith('.xz') else open(p, 'r', encoding='utf-8')

def stream_to_cache(paths, prefix, fixed_domain=None):
    """逐行流式读取原始 jsonl(.xz)，按 CHUNK 行写入 xz 压缩的 CSV 分卷。"""
    for old in CACHE.glob(prefix + '_part*.csv.xz'):
        old.unlink()
    n, part, fo, w, t0 = 0, 0, None, None, time.time()
    for p in paths:
        print('  流式读取', p)
        with open_any(p) as f:
            for line in f:
                line = line.strip()
                if not line: continue
                '''try:
                    obj = json.loads(line)
                except Exception:
                    continue'''
                try:
                    obj = json.loads(line)
                except Exception as e:
                    # 只打印前5条报错信息，防止刷屏
                    if not hasattr(stream_to_cache, 'err_count'):
                        stream_to_cache.err_count = 0
                    if stream_to_cache.err_count < 5:
                        print(f"\n[解析错误] 异常信息: {e}")
                        print(f"[解析错误] 出错行内容(前100字符): {repr(line[:100])}")
                        stream_to_cache.err_count += 1
                    continue
                if fo is None or n % CHUNK == 0:
                    if fo is not None: fo.close()
                    part += 1
                    fo = lzma.open(CACHE / ('%s_part%02d.csv.xz' % (prefix, part)), 'wt', encoding='utf-8', newline='')
                    w = csv.DictWriter(fo, fieldnames=OUT_COLS); w.writeheader()
                dom = fixed_domain if fixed_domain else norm_domain(obj.get('_source_domain'))
                w.writerow(compress_record(obj, dom)); n += 1
                if n % 20000 == 0: print('    已处理 %d 条, %.0fs' % (n, time.time() - t0))
    if fo is not None: fo.close()
    print('  完成 %d 条 -> %d 个分卷, %.0fs' % (n, part, time.time() - t0))

def load_signals(prefix, raw_paths, fixed_domain=None):
    parts = sorted(CACHE.glob(prefix + '_part*.csv.xz'))
    if not parts:
        if not raw_paths:
            raise FileNotFoundError('既没有缓存也没有原始文件: ' + prefix)
        stream_to_cache(raw_paths, prefix, fixed_domain)
        parts = sorted(CACHE.glob(prefix + '_part*.csv.xz'))
    df = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    print('[%s] %d 个分卷 -> %d 条记录' % (prefix, len(parts), len(df)))
    return df

RAW_A1 = [p for p in [DATA / 'slimpajama_quality_signal_sample.jsonl.xz'] if p.exists()] or \
         [p for p in DATA.glob('slimpajama_quality_signal_sample.jsonl*/slimpajama_quality_signal_sample.jsonl') if p.is_file()]
RAW_A2 = sorted((DATA / 'slimpajama_quality_extended').glob('arxiv_*.jsonl.xz'))
RAW_A3 = sorted((DATA / 'slimpajama_quality_extended').glob('github_*.jsonl.xz'))
print('原始文件: A1', [p.name for p in RAW_A1], '| A2', [p.name for p in RAW_A2], '| A3', [p.name for p in RAW_A3])
