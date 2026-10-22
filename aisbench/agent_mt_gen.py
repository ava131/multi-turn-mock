# -*- coding: utf-8 -*-
"""AISBench 自定义配置：直接读取本仓库生成的 LongBench 风格 jsonl。

用法：
    # 1) 改下面 dataset_path 为 jsonl 的绝对路径
    # 2) 把 models 换成你自己的推理服务配置（或直接把 datasets 拷进现有 perf 配置）
    ais_bench --config aisbench/agent_mt_gen.py -m all

为什么需要这个文件：
    AISBench 的 --custom-dataset-path 默认走的是 custom qa 配置，它要求
    question / answer 字段，而 LongBench v1 用的是 input / context / answers，
    所以会报 KeyError: "Column answer not in the dataset"。
    这里显式声明 input_columns / output_column，字段就对上了。
"""
from ais_bench.benchmark.datasets import CustomDataset
from ais_bench.benchmark.models import VLLMCustomAPIChat
from ais_bench.benchmark.openicl.icl_evaluator import AccEvaluator
from ais_bench.benchmark.openicl.icl_inferencer import GenInferencer
from ais_bench.benchmark.openicl.icl_prompt_template import PromptTemplate
from ais_bench.benchmark.openicl.icl_retriever import ZeroRetriever

# ── 改成实际的 jsonl 绝对路径 ────────────────────────────────────────────
dataset_path = "/absolute/path/to/multi-turn-mock/datasets/agent_mt_32k_3x20.jsonl"

agent_mt_reader_cfg = dict(
    input_columns=["context", "input"],   # 长上下文 + 本轮问题
    output_column="answers",              # LongBench v1 的答案字段（list）
)

agent_mt_infer_cfg = dict(
    prompt_template=dict(
        type=PromptTemplate,
        template=dict(
            round=[
                dict(role="HUMAN", prompt="{context}\n\n{input}"),
            ],
        ),
    ),
    retriever=dict(type=ZeroRetriever),
    inferencer=dict(type=GenInferencer),
)

agent_mt_eval_cfg = dict(evaluator=dict(type=AccEvaluator), pred_role="BOT")

datasets = [
    dict(
        abbr="agent_mt",
        type=CustomDataset,
        path=dataset_path,
        reader_cfg=agent_mt_reader_cfg,
        infer_cfg=agent_mt_infer_cfg,
        eval_cfg=agent_mt_eval_cfg,
    )
]

# ── 模型：按你的环境改；性能测试请换成 stream/perf 的模型配置 ──────────────
models = [
    dict(
        attr="service",
        type=VLLMCustomAPIChat,
        abbr="vllm-chat",
        path="",
        model="",
        request_rate=0,
        retry=2,
        host_ip="127.0.0.1",
        host_port=8000,
        max_out_len=512,
        batch_size=1,
    )
]

work_dir = "outputs/agent_mt/"
