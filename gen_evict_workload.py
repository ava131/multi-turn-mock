#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构造“驱逐-复用”型压测负载：热前缀被容量挤掉，复用时 baseline miss、
带 offload/保留策略的方法 hit。

负载形状：
    [热前缀 H] -> N 条冷请求（各自独占前缀） -> 复用 H 的新请求 -> 再来 N 条冷 -> 复用 ...
冷请求的总 KV 超过容量，把 H 的块按 LRU 挤出去；复用请求与 H 共享 H 长度前缀。

先跑内置的块级 LRU 模拟，确认 baseline 确实驱逐了 H，再输出 jsonl。
"""
import argparse
import json
import os
import random
import sys

BLOCK = 16  # 与 vLLM 默认 block_size 对齐


def simulate(capacity_tokens, hot_tokens, cold_tokens, n_cold, revisits):
    """块级 LRU 模拟，返回 (baseline 命中, 理想命中, 总块数)。

    baseline：热块和其他块一样参与 LRU；
    理想：热块被 pin 住（相当于 offload 到 host 后按需取回），冷请求只能用剩下的容量。
    """
    from collections import OrderedDict
    cap = max(1, capacity_tokens // BLOCK)
    hot = [("hot", i) for i in range(hot_tokens // BLOCK)]
    cold = [("cold", i) for i in range(cold_tokens // BLOCK)]

    def run(pin_hot):
        cache = OrderedDict()
        reserved = set(hot) if pin_hot else set()
        cap_eff = max(1, cap - len(reserved))
        hits = total = 0
        revisit_hits = []

        def access(blocks):
            nonlocal hits, total
            for b in blocks:
                total += 1
                if b in reserved:
                    hits += 1           # pin 住的块：复用即命中
                    continue
                if b in cache:
                    hits += 1
                    cache.move_to_end(b)
                else:
                    cache[b] = 1
                    if len(cache) > cap_eff:
                        cache.popitem(last=False)

        access(hot)                     # 第 1 次：热前缀本身（miss）
        for r in range(revisits):
            for c in range(n_cold):
                access([(f"cold_{r}_{c}", i) for i in range(cold_tokens // BLOCK)])
            before = hits
            access(hot + [("suffix", r)])   # 复用请求：热前缀 + 新问题
            revisit_hits.append(hits - before)
        return hits, total, revisit_hits

    b_hits, total, b_rv = run(False)
    i_hits, _, i_rv = run(True)
    return b_hits, i_hits, total, b_rv, i_rv


def build_text(tokens, chars_per_token, rng, tag):
    n = max(1, int(tokens * chars_per_token))
    out = []
    while sum(len(x) for x in out) < n:
        out.append("%s 第 %d 段：%s" % (tag, len(out) + 1, "数据块" * rng.randint(3, 8)))
    return "".join(out)[:n]


def main():
    p = argparse.ArgumentParser(description="生成驱逐-复用型负载")
    p.add_argument("--capacity-tokens", type=int, default=64000,
                   help="KV 池容量（token），按你的显存/模型折算")
    p.add_argument("--hot-tokens", type=int, default=32000, help="热前缀长度")
    p.add_argument("--cold-tokens", type=int, default=8000, help="每条冷请求长度")
    p.add_argument("--cold-count", type=int, default=30, help="两次复用之间插入的冷请求数")
    p.add_argument("--revisits", type=int, default=3, help="复用次数")
    p.add_argument("--chars-per-token", type=float, default=1.6, help="中文近似比例")
    p.add_argument("--format", choices=["gsm8k", "v1"], default="gsm8k")
    p.add_argument("--dataset", default="evict_mock")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--out", default="evict_workload.jsonl")
    p.add_argument("--trace", default="evict_workload.trace.json")
    args = p.parse_args()

    rng = random.Random(args.seed)
    hot_prefix = build_text(args.hot_tokens, args.chars_per_token, rng, "热")
    hot_q = "请基于上面的材料继续分析，并给出结论。"

    records, trace = [], []
    cold_id = 0

    def emit(prefix, kind, shared, idx):
        q = hot_q if kind == "hot" else "请基于上面的材料回答问题 %d。" % idx
        ans = "结论：基于材料 %s 的结论。" % kind
        if args.format == "gsm8k":
            rec = {"question": prefix + "\n\n" + q, "answer": ans}
        else:
            rec = {"input": q, "context": prefix, "answers": [ans],
                   "length": len(prefix) + len(q) + len(ans),
                   "dataset": args.dataset, "language": "zh",
                   "all_classes": None, "_id": "r%04d" % idx}
        records.append(rec)
        trace.append({"index": idx, "kind": kind, "tokens": int(len(prefix) / args.chars_per_token),
                      "shared_prefix_tokens": shared, "arrival_ms": idx * 100})

    emit(hot_prefix, "hot", 0, 0)
    idx = 1
    for r in range(args.revisits):
        for _ in range(args.cold_count):
            cold_id += 1
            emit(build_text(args.cold_tokens, args.chars_per_token, rng, "冷%d" % cold_id),
                 "cold", 0, idx)
            idx += 1
        emit(hot_prefix, "revisit", args.hot_tokens, idx)
        idx += 1

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(args.trace, "w", encoding="utf-8") as f:
        json.dump({"capacity_tokens": args.capacity_tokens,
                   "hot_tokens": args.hot_tokens,
                   "cold_tokens": args.cold_tokens,
                   "cold_count": args.cold_count,
                   "revisits": args.revisits,
                   "requests": trace}, f, ensure_ascii=False, indent=2)

    baseline, ideal, total, b_rv, i_rv = simulate(
        args.capacity_tokens, args.hot_tokens, args.cold_tokens,
        args.cold_count, args.revisits)
    print("请求数 %d（1 热 + %d×(冷+复用)）" % (len(records), args.revisits), file=sys.stderr)
    print("KV 容量 %d tokens | 热前缀 %d | 冷请求 %d × %d"
          % (args.capacity_tokens, args.hot_tokens, args.cold_tokens, args.cold_count),
          file=sys.stderr)
    print("块级模拟（总 %d 块）：baseline 命中 %d（%.1f%%）| pin 热前缀 命中 %d（%.1f%%）"
          % (total, baseline, baseline / max(total, 1) * 100,
             ideal, ideal / max(total, 1) * 100), file=sys.stderr)
    print("每次复用命中的块数：baseline %s | pin %s（热前缀共 %d 块）"
          % (b_rv, i_rv, args.hot_tokens // BLOCK), file=sys.stderr)
    print("已写入 %s 与 %s" % (args.out, args.trace), file=sys.stderr)


if __name__ == "__main__":
    main()
