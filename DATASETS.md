# 多轮对话 / 请求轨迹 数据集现状

分两类：

- **A. 对话语料**：有文本，没有逐轮到达时间；
- **B. 请求轨迹（trace）**：有到达时间 / 前缀关系，没有文本。

所有数字都是**本次抽样实测**，样本量写在各小节末尾，不是论文数字。

## 目录

- [A. 对话语料](#a-对话语料有文本无逐轮到达时间)
  - [A1. WildChat-1M](#a1-wildchat-1m) · [A2. ShareGPT](#a2-sharegpt) · [A3. MT-Bench](#a3-mt-bench) · [A4. LoCoMo](#a4-locomo) · [A5. LongMemEval](#a5-longmemeval) · [A6. InfiniteBench](#a6-infinitebenchendia--zhdia) · [A7. LMSYS-Chat-1M](#a7-lmsys-chat-1m)
- [B. 请求轨迹](#b-请求轨迹有到达时间前缀关系无文本)
  - [B1. BurstGPT](#b1-burstgpt-v2) · [B2. Azure trace](#b2-azure-llm-inference-trace-2023splitwise) · [B3. Mooncake](#b3-mooncake--kimi-trace)
- [同一 ID 的请求间隔](#同一-id-的请求间隔trace) · [汇总](#汇总) · [怎么用](#怎么用这份整理) · [测量方法](#测量方法)

---

## A. 对话语料（有文本，无逐轮到达时间）

### A1. WildChat-1M

- 来源：AI2 的免费 WildChat 服务，真实用户 ↔ ChatGPT（GPT-3.5/GPT-4）对话
- 链接：<https://huggingface.co/datasets/allenai/WildChat-1M>
- 规模：1,000,000 段
- 字段：`conversation / model / timestamp / language / toxic / redacted / country / header`
- 许可：ODC-BY
- 长度：字符中位 **2,259**、p90 10,831、p99 32,653、max 50,976；轮数中位 4、max 36；约 **600 tokens/段**

示例 1（英文，2 轮，医疗问答）：

```
[user]      Old age PT hx of DM, HTN, dyslipidemia His ECG I.II, aVF (MI)
            what is the highest risk factor for this condition?
[assistant] The highest risk factor for this condition (myocardial infarction, MI)
            in this patient would be old age combined with a history of diabetes...
```

示例 2（中文，4 轮，话题跳变）：

```
[user]      如何在sd上无错误进行模型训练
[assistant] 在SD卡上进行模型训练的过程通常包括以下几个步骤：1. 准备数据和环境...
[user]      作为一名室内设计师该如何在网上快速找到客户
[assistant] 作为一名室内设计师，在网上快速找到客户可以通过以下途径：1. 展示作品...
```

样本：500 段随机抽样。

### A2. ShareGPT

- 来源：社区分享的 ChatGPT 对话，`philschmid/sharegpt-raw` 清洗版
- 链接：<https://huggingface.co/datasets/philschmid/sharegpt-raw>
- 规模：约 9 万段
- 字段：`id / conversations[{from, value}]`
- 长度：以几千 token 以内为主（未做全量统计）

示例（中文，4 轮，法律咨询）：

```
[human] 我们公司珠海市五一一八科技有限公司开发了一个chrome浏览器插件...
[gpt]   尊敬的法官：我代表珠海市五一一八科技有限公司，就百度公司...
[human] continue
[gpt]   虑我们的辩护意见，并能够公正地判断此事的真相...
```

### A3. MT-Bench

- 来源：LMSYS 高质量多轮问题集
- 链接：<https://github.com/lm-sys/FastChat/blob/main/fastchat/llm_judge/data/mt_bench/question.jsonl>
- 规模：80 题 × 2 轮
- 字段：`question_id / category / turns`
- 长度：总字符平均 **404**、中位 285、max 1,756（约 150 tokens）

示例 1（writing, id=81）：

```
Q1 Compose an engaging travel blog post about a recent trip to Hawaii...
Q2 Rewrite your previous response. Start every sentence with the letter A.
```

示例 2（writing, id=82）：

```
Q1 Draft a professional email seeking your supervisor's feedback on the 'Quarterly Financial Report'...
Q2 Take a moment to evaluate and critique your own response.
```

样本：全量 80 题。

### A4. LoCoMo

- 来源：Snap，长期对话记忆研究
- 链接：<https://github.com/snap-research/locomo>
- 规模：论文 50 段，公开 10 段
- 特点：多 session、超长闲聊 + QA
- 长度：第 1 段 **448 轮 / 53,049 字符 ≈ 13k tokens**；论文平均约 9k

示例（同一段对话开头）：

```
[Speaker_1] Hey Carol! Nice to see you again. I've been keeping busy since Friday,
            cause I went hiking in the mountains with my friends. It was awesome!
[Speaker_2] Hey Roy! Nice to see you too! You will not believe it, but I've just
            moved with my dogs to a town with stunning mountain views.
```

样本：公开 10 段中的第 1 段。

### A5. LongMemEval

- 来源：UCLA 等，ICLR 2025，测试聊天助手的长期记忆
- 链接：<https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned>
- 规模：500 条问题，每条配一段长聊天历史（多 session、带时间戳）
- 长度：S 版约 **115k tokens**，M 版百万级（论文口径）
- 说明：是“长历史 + 记忆类 QA”，不是对话语料；历史里带 session 时间戳，但逐轮时间未公开

### A6. InfiniteBench（En.Dia / Zh.Dia）

- 来源：OpenBMB 100k+ 长上下文基准
- 链接：<https://github.com/OpenBMB/InfiniteBench>
- En.Dia：**200 条，平均输入 103.6k tokens**（剧本式长对话，识别说话人）
- 中文版 `Zh.Dia` 同结构

### A7. LMSYS-Chat-1M

- 来源：LMSYS，真实用户与 25 个模型的对话
- 链接：<https://huggingface.co/datasets/lmsys/lmsys-chat-1m>
- 规模：100 万段、150+ 语言
- 获取：**gated**（需同意，研究用途），本次未取样

---

## B. 请求轨迹（有到达时间/前缀关系，无文本）

### B1. BurstGPT v2

- 来源：HKUST(GZ)，微软 Azure 上真实 ChatGPT/GPT-4 流量
- 链接：<https://github.com/HPMLL/BurstGPT>
- 规模：约 529 万条请求 / 121 天
- 字段：`Timestamp / Session ID / Elapsed time / Model / Request tokens / Response tokens / Total tokens / Log Type`
- 长度：请求 token 平均 **625**、响应平均 **245**、max 3,407
- 说明：`Session ID` 只出现在 `Conversation log`，`API log` 为空
- 时序：同一 Session 相邻请求间隔 **中位 178 秒、平均 4,765 秒**（长尾很大，p90 3,226 秒）；每会话平均 3.70 条请求（中位 2，max 191）；全局到达间隔平均 1.62 秒

示例：

```
Timestamp,Session ID,Elapsed time,Model,Request tokens,Response tokens,Total tokens,Log Type
19440110.0,1722ac82-0a46-4bf0-aa08-89794e7a2b3f,43,GPT-4,906,446,1352,Conversation log
```

样本：`BurstGPT_3.csv` 前 50 MB（1,242,541 条请求、8,281 个会话）。

### B2. Azure LLM Inference Trace 2023（Splitwise）

- 来源：微软 Azure 生产推理服务，2023-11-16 采样
- 链接：<https://github.com/Azure/AzurePublicDataset/blob/master/AzureLLMInferenceDataset2023.md>
- 规模：conversation trace **19,366 条**；另有 code trace
- 字段：`TIMESTAMP / ContextTokens / GeneratedTokens`
- 长度：上下文平均 **1,155** tokens、生成平均 **211**、max 14,050
- 时序：**没有 session id**，只能算全局到达间隔——19,366 条 / 3,502 秒，平均 **0.18 秒**（中位 0.118 秒）
- 短板：没有 session id、没有文本（隐私原因）

示例：

```
TIMESTAMP,ContextTokens,GeneratedTokens
2023-11-16 18:15:46.6805900,374,44
2023-11-16 18:15:50.9951690,396,109
```

样本：全量 19,366 行。

### B3. Mooncake / Kimi trace

- 来源：Moonshot（Kimi），FAST'25 论文配套数据
- 链接：<https://github.com/kvcache-ai/Mooncake/tree/main/FAST25-release/traces>
- 规模：**12,031 条请求**，时间跨度 0 ~ 3,536,999（秒）
- 字段：`timestamp / input_length / output_length / hash_ids`
- 长度：输入平均 **12,035** tokens、输出平均 343、max 126,195
- `hash_ids`：前缀块哈希（块大小约 512 token），直接描述前缀共享
- 复用：**42.5%** 的请求有 ≥50% 前缀可复用；共享 token 中位 512、p90 12,800、max 122,880
- 时序：同一个 hash 块相邻两次被引用的间隔 **中位 113,999 秒（≈31.7 小时）、平均 212,905 秒**，p90 519,000 秒；全局到达间隔平均 294 秒

示例：

```json
{"timestamp": 0, "input_length": 6758, "output_length": 500, "hash_ids": [0,1,2,...,13]}
{"timestamp": 0, "input_length": 7322, "output_length": 490, "hash_ids": [0,14,15,...,27]}
```

第二条只共享块 0、之后是新块——典型的“同前缀、新内容”。

样本：全量 12,031 行。

---

## 同一 ID 的请求间隔（trace）

“同一个 ID”在三份 trace 里的含义不同：

| trace | ID 是什么 | 同一 ID 的相邻请求间隔 |
|---|---|---|
| BurstGPT | `Session ID`（会话） | 中位 **178 秒**、平均 **4,765 秒**、p90 3,226 秒（长尾到 18 天） |
| Azure trace | 无 ID | 无法计算；全局到达间隔平均 **0.18 秒** |
| Mooncake | `hash_ids` 里的前缀块 | 同一块被再次引用：中位 **113,999 秒**、平均 **212,905 秒**、p90 519,000 秒 |

可以这样理解：

- **BurstGPT / Mooncake** 都有“同一份前缀隔很久才被再次用到”的现象，只是 BurstGPT 以会话为单位、Mooncake 以块为单位；
- **Azure** 完全没有会话信息，只能当到达率样本用。

## 汇总

| 数据集 | 文本 | 逐轮到达时间 | 前缀/会话关系 | 同一 ID 间隔 |
|---|---|---|---|---|
| WildChat-1M | ✅ | ❌（仅会话级时间戳） | ❌ | — |
| ShareGPT | ✅ | ❌ | 会话内顺序 | — |
| MT-Bench | ✅ | ❌ | 2 轮 | — |
| LoCoMo | ✅ | ❌ | 多 session | — |
| LongMemEval | ✅ | ⚠️（session 时间戳） | 多 session | — |
| InfiniteBench En.Dia | ✅ | ❌ | 长对话 | — |
| LMSYS-Chat-1M | ✅ | ❌ | 会话 | — |
| BurstGPT | ❌ | ✅ | ✅ Session ID | 中位 178 秒 / 平均 4,765 秒 |
| Azure trace | ❌ | ✅ | ❌ | 无 ID；全局 0.18 秒 |
| Mooncake trace | ❌ | ✅ | ✅ hash_ids | 同块 中位 113,999 秒 |

**结论**：没有任何一个数据集同时具备「文本 + 逐轮到达时间 + 前缀关系」。trace 提供时间/长度/前缀结构，文本需要另行合成或拼接。

## 怎么用这份整理

1. **需要真实多轮文本**：WildChat / ShareGPT / LoCoMo / LongMemEval / InfiniteBench；
2. **需要真实到达节奏**：BurstGPT（会话级）或 Azure（只给全局速率）；
3. **需要真实前缀复用关系**：Mooncake 的 `hash_ids` 最直接；
4. **需要“驱逐-复用”特定 case**：用本仓库 `gen_evict_workload.py` 按容量参数构造。

## 测量方法

| 数据集 | 样本 |
|---|---|
| WildChat-1M | 500 段随机抽样（HF datasets-server 分页） |
| ShareGPT | 1 段示例（未统计全量长度） |
| MT-Bench | 全量 80 题 |
| LoCoMo | 公开 10 段中的第 1 段 |
| LongMemEval / InfiniteBench / LMSYS | 引用论文或 README 口径，未本地复测 |
| BurstGPT | `BurstGPT_3.csv` 前 50 MB（1,242,541 条） |
| Azure trace | 全量 19,366 行 |
| Mooncake | 全量 12,031 行 |

token 估算：英文按 4 字符/token，中文按 1.6 字符/token；精确值需用对应模型 tokenizer。
