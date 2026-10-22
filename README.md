# 多轮对话 mock 数据集

生成 **LongBench v1 格式**的多轮对话 jsonl，用于推理服务的**纯性能压测**（前缀缓存命中、批量调度、KV 占用），不用于精度评测。

- 每条 jsonl = 一次请求，字段与 LongBench v1 官方完全对齐（8 个字段）
- 所有请求共享同一段 system prompt（逐字节一致）
- 第 t 轮请求的 `context` 逐字节包含前 t-1 轮的问答原文，按文件顺序发送即可命中前缀缓存
- 内容由「场景库 + 模板」合成，零依赖、可复现，不联网、不调用模型
- 可选 **长文档模式**：用 LongBench v1 的真实长上下文拼出 ~32k 的基底，每轮再增长 ~0.5k

## 目录结构

```
multi-turn-mock/
├── README.md                     # 本文件
├── gen_multiturn_longbench.py    # 生成脚本（Python 3.8–3.13，仅标准库）
├── scenarios.json                # 场景库：zh 56 个 + en 8 个
└── datasets/
    ├── agent_mt_3x20.jsonl       # 示例：3 轮 × 20 用户 = 60 条（短上下文）
    ├── agent_mt_32k_3x20.jsonl   # 示例：3 轮 × 20 用户，每条 ~32k 字符（4.9 MB）
    ├── agent_mt_32k_shuffle_3x20.jsonl # 示例：3 轮 × 20 用户，按用户打乱填充到 32k（5.1 MB）
    ├── agent_mt_v2_32k_3x20.jsonl # 示例：同上内容，字段对齐 LongBench v2 单选格式（5.1 MB）
    └── agent_mt_32k_3x3.jsonl    # 示例：3 轮 × 3 用户，每条 ~32k 字符（方便快速查看）
```

## 快速开始

```bash
# 默认：3 轮 × 每轮 20 用户 = 60 条，输出 ./agent_mt.jsonl
python3 gen_multiturn_longbench.py

# 推荐：直接生成到 datasets/
python3 gen_multiturn_longbench.py --num-turns 3 --users-per-turn 20 \
    --out datasets/agent_mt_3x20.jsonl

# 每轮人数不同（第 3 轮只剩前 10 个用户）
python3 gen_multiturn_longbench.py --num-turns 3 --users-per-turn 20,20,10 \
    --out datasets/agent_mt_20_20_10.jsonl

# 拉长上下文（每条约 2k tokens 以上），加大回答长度
python3 gen_multiturn_longbench.py --num-turns 5 --users-per-turn 20 \
    --system-chars 2000 --user-chars 300 --answer-chars 800 \
    --out datasets/agent_mt_big.jsonl

# 长文档模式：从 LongBench 真实文档拼 ~32k 基底，每轮 +0.5k
python3 gen_multiturn_longbench.py --doc-source /path/to/LongBench/data/dureader.jsonl \
    --num-turns 3 --users-per-turn 20 --out datasets/agent_mt_32k.jsonl

# 英文
python3 gen_multiturn_longbench.py --language en --num-turns 2 \
    --users-per-turn 10 --out datasets/agent_mt_en.jsonl
```

脚本每次写完都会**自校验**：字段集合、行数、`_id` 唯一性、前缀链是否逐字节衔接、`answers`/`length`/`all_classes` 类型。任一不满足直接报错退出（退出码非 0）。

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--num-turns` | `3` | 对话轮数 |
| `--users-per-turn` | `20` | 每轮的用户/请求数。单个整数会套用到每一轮；也可写成 `20,20,10`（长度不足时用最后一个值补齐，超长时截断） |
| `--scenarios` | 脚本同目录 `scenarios.json` | 场景库路径 |
| `--doc-source` | 无 | LongBench 格式的 jsonl 或目录（取 `context` 作为长文档池）。不给就是纯合成短上下文 |
| `--base-len` | `0` | 基础长上下文目标长度；单位跟随语言（中文=字符，英文=词）。不给 `--doc-source` 时表示把 system prompt 重复到该长度 |
| `--pad-mode` | `shuffle` | 没有 `--doc-source` 时如何填 `--base-len`：`shuffle` 每个用户用自己的内容打乱（前缀不同）；`system` 重复 system（前缀相同，极端场景） |
| `--doc-field` | 自动探测 | 长文本字段名；依次尝试 `context`/`prompt`/`text`/`input`/`content`/`document`/`doc` |
| `--doc-verbatim` | 关闭 | 每条记录**原样**作为基底，不拼接、不截断（适合已经切好 32k token 的 jsonl） |
| `--doc-mode` | `distinct` | `distinct` 每个用户不同文档；`shared` 所有用户同一份（前缀完全共享） |
| `--system-chars` | `600` | system prompt 目标长度（中文=字符，英文=词） |
| `--user-chars` | `150` | 每轮用户提问目标长度 |
| `--answer-chars` | `350` | 每轮助手回答目标长度（150+350 ≈ 每轮 +0.5k） |
| `--language` | `zh` | `zh` 按字符计长度，`en` 按词计长度 |
| `--dataset` | `agent_mt` | 写入 `dataset` 字段的值 |
| `--sep` | `\n\n` | 消息分隔符（影响前缀拼接方式） |
| `--seed` | `42` | 随机种子；同 seed 输出逐字节一致 |
| `--out` | `agent_mt.jsonl` | 输出路径（目录不存在会自动创建） |
| `--manifest` | 无 | 额外输出一份行号/`_id` 映射 json |
| `--no-verify` | 关闭 | 跳过写后校验 |

长度类参数的语义是「目标值」：素材不够会循环铺长，超了会在句末（`。`/换行）处截断，因此实际长度略小于等于目标值。

## 长文档模式（~32k 上下文）

默认模式只有几百字符的 system prompt，做 KV/前缀缓存压测时输入太短。用 `--doc-source` 指定 LongBench v1 数据后，每条请求的 `context` 会变成：

```
system prompt（所有请求共享）
+ 真实长文档（~32k，来自 LongBench 的 context 字段，多个文档拼接而成）
+ 前 t-1 轮问答（每轮约 +0.5k）
```

### 数据从哪来

用你已有的 LongBench v1 数据即可，不需要额外下载：

- AISBench 部署的目录：`ais_bench/datasets/LongBench/data/`
- 或官方 `data.zip` 解压后的 `data/` 目录

```bash
# 单个任务（推荐，中文用 dureader / multifieldqa_zh，英文用 gov_report / multi_news）
python3 gen_multiturn_longbench.py --doc-source ais_bench/datasets/LongBench/data/dureader.jsonl ...

# 整个目录：会把目录下所有 *.jsonl 的 context 汇总成文档池
python3 gen_multiturn_longbench.py --doc-source ais_bench/datasets/LongBench/data ...
```

### 长度怎么算

- `--base-len 32000`：中文按**字符**、英文按**词**，多个文档按顺序拼接后截断到该长度（在段落/句子边界截断）
- 每轮增长 ≈ `--user-chars + --answer-chars`，默认 `150 + 350 = 500`，所以 3 轮的上下文约为 `32k → 32.5k → 33k`
- 注意：`32000` 是字符数，不是 token 数。中文大约 1 token ≈ 1.5–1.7 字符，所以 32k 字符 ≈ 19k–21k tokens；想要 ~32k tokens 就把 `--base-len` 调到 `50000` 左右（或按你模型的实际 tokenizer 换算）

### 不依赖外部数据：按用户打乱填充到 32k

```bash
python3 gen_multiturn_longbench.py \
    --base-len 32000 \
    --num-turns 3 --users-per-turn 20 \
    --out datasets/agent_mt_32k.jsonl
```

`--pad-mode` 默认是 `shuffle`：

- 每个用户用自己的场景生成一批问答片段（约 2 倍所需数量），**打乱后**拼到 `--base-len`，组成 `system + 填充块`
- 不同用户的场景/片段/顺序都不同，所以**前 32k 各不相同**（20 条 t1 的公共前缀只有 system 的 ~590 字符，约 1.8%）
- 同一用户的基底在生成时就固定，后两轮继续只追加问答，前缀链不变
- 填充块开头有一行 `材料编号 uXX｜场景 ...`，保证**不同用户在 system 之后立刻分叉**（实测跨用户最大公共前缀 = system 长度，约 599 字符）
- 填充块内部会有重复（同一批片段被打乱后可能再次使用），这是为了凑长度，不影响前缀分布

如果想复现旧的“所有请求前缀完全相同”的极端场景，用：

```bash
python3 gen_multiturn_longbench.py --base-len 32000 --pad-mode system ...
```

此时 20 条 t1 的 `context` 逐字节相同，全部命中前缀缓存——只适合做极端压测，不代表真实用户。

### 用你自己已经切好的 32k jsonl### 用你自己已经切好的 32k jsonl

如果你手上已经有一份 jsonl，每行的某个字段就是切好的 ~32k token 文本，直接：

```bash
python3 gen_multiturn_longbench.py \
    --doc-source my_32k.jsonl \
    --doc-verbatim \
    --doc-field prompt \
    --system-chars 0 \
    --num-turns 3 --users-per-turn 20 \
    --out datasets/agent_mt_32k.jsonl
```

- `--doc-verbatim`：每条记录原样当基底，**不拼接、不截断**，第 1 轮的 `context` 就是这条记录本身
- `--doc-field`：字段名，不写会按上面的顺序自动探测（会打印 `文档字段: 'prompt' | 文档数: 20`）
- `--system-chars 0`：不加 system prompt。这样第 1 轮 `context` 与源记录**逐字节一致**；如果保留默认的 600 字符 system，则 `context = system + 记录`
- 记录条数少于单轮用户数时会循环复用并打印警告

后续每轮仍然只追加“用户提问 + 助手回答”，默认约 +500 字符（≈ 300 tokens）；想要每轮 +500 tokens，把它调到 `--user-chars 260 --answer-chars 660` 左右（中文字符/token 比约 1.6）。

### 两种文档分配

| `--doc-mode` | 行为 | 用途 |
|---|---|---|
| `distinct`（默认） | 每个用户从文档池不同位置取文档 | 模拟 20 个不同用户各自贴长材料，前缀各不相同 |
| `shared` | 所有用户用同一份文档 | 20 条请求共享完整 ~32k 前缀，专门压前缀缓存命中 |

`shared` 模式下第 1 轮 20 条请求的 `context` 完全相同（实测唯一前缀数 = 1）；`distinct` 模式下只有 system prompt 那段共享。

### 效果示例（dureader，base-len 32000）

```
t1  ctx 32253 字符
t2  ctx 32738 字符（+485）
t3  ctx 33226 字符（+488）
```

## 对齐 LongBench v2 字段（`--format v2`）

LongBench v2 是**单选**格式，字段是：

```json
{"_id": "...", "domain": "...", "sub_domain": "...", "difficulty": "easy|hard",
 "length": "short|medium|long", "question": "...",
 "choice_A": "...", "choice_B": "...", "choice_C": "...", "choice_D": "...",
 "answer": "A|B|C|D", "context": "..."}
```

加 `--format v2` 就能输出这一套：

```bash
python3 gen_multiturn_longbench.py --format v2 \
    --base-len 32000 --num-turns 3 --users-per-turn 20 \
    --out datasets/agent_mt_v2_32k.jsonl
```

字段映射：

| v2 字段 | 取值 |
|---|---|
| `context` | system + 长文档 + 前 t-1 轮问答（多轮仍然靠它携带历史） |
| `question` | 本轮用户提问 |
| `choice_A`–`choice_D` | 4 个选项，其中一个是本轮合成的回答，另外 3 个是场景相关的干扰项 |
| `answer` | 正确项字母，分布近似均匀（A/B/C/D） |
| `difficulty` | `easy` / `hard` 随机 |
| `length` | v2 的**类别**字段：`short` / `medium` / `long`（阈值 16k / 64k 字符，是我们自己定的；v2 官方按词数划分） |
| `domain` / `sub_domain` | 场景的 `domain` 与 `style` |
| `_id` | `uXX_tY` |

注意：

- v2 是**单轮单选**，没有多轮概念；多轮依然是靠 `context` 里带历史、每轮一个独立请求实现的
- 选项内容是占位：`answer` 只对得上我们自己造的四个选项，没有真实语义，纯压测足够
- AISBench 的 `longbenchv2` 配置用 `load_dataset('json', data_files=path)` 读取，**jsonl 也能直接读**；把配置里的 `path` 指向本文件即可

## 输出格式

每行一个 JSON 对象，字段与 LongBench v1 一致（顺序也保持一致）：

```json
{
  "input": "帮我看下payment-api 的 5xx 比例，周六 10:05开始不太对，先给个初步结论。\n补充信息：...",
  "context": "你是一个知识面较广的智能助手，服务于「示例科技」。...\n\n<第1轮问题>\n\n<第1轮回答>",
  "answers": ["结论：关于payment-api 的 5xx 比例，异常主要集中在...\n\n证据：\n- ...\n\n建议：\n- ..."],
  "length": 988,
  "dataset": "agent_mt",
  "language": "zh",
  "all_classes": null,
  "_id": "u00_t1"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `input` | string | 本轮用户提问（对应 LongBench 的短输入） |
| `context` | string | system prompt + 前 t-1 轮对话；第 1 轮就是纯 system |
| `answers` | list[string] | 占位回答，**不是标准答案**（压测不看精度） |
| `length` | int | `input + context + answers` 的长度，中文按字符、英文按词 |
| `dataset` | string | 数据集名，默认 `agent_mt` |
| `language` | string | `zh` / `en` |
| `all_classes` | null | 非分类任务固定为 `null` |
| `_id` | string | `u<用户号>_t<轮次>`，如 `u07_t2` |

## 顺序与语义（重点）

**文件按轮次优先排序**：先第 1 轮的 20 条，再第 2 轮的 20 条，再第 3 轮的 20 条。直接按行顺序发送，就对应「bs 0–20 / 20–40 / 40–60」。

**system prompt 全局共享**：所有请求的前 N 个字符（默认约 590 字符）完全一致；从该用户第一个问题开始分叉。

**长文档基底**：开了 `--doc-source` 后，`context` 的固定部分是 `system + 长文档`，此后每轮只追加问答（约 +0.5k）。

**前缀链保证**：对同一用户，

```
context(t) == context(t-1) + sep + input(t-1) + sep + answers(t-1)[0]
```

所以第 2、3 轮能命中第 1 轮建立的 KV 前缀。注意：实际推理模板必须把 `context` 放在 `input` 之前（LongBench 官方模板都是这个顺序），并且不要在中途重新排版，否则前缀就断了。

### `--users-per-turn` 的不同情况

用户编号从 `u00` 开始，第 t 轮参与的是「编号 < 该轮人数」的用户。

| 写法 | 总条数 | 结果 |
|---|---|---|
| `20,20,20` | 60 | 20 个用户各 3 轮，`u00_t1 … u19_t3` |
| `20,20,10` | 50 | `u00`–`u09` 有 3 轮；`u10`–`u19` 停在第 2 轮。最后 10 行是 `u00_t3 … u09_t3` |
| `5,8,3` | 16 | 共 8 个用户：`u00`–`u02` 3 轮，`u03`/`u04` 2 轮，`u05`–`u07` 从第 2 轮才开始（context 只有 system，是新会话） |
| `20,10,20` | 50 | `u10`–`u19` 第 2 轮缺席、第 3 轮回归时**会接上自己第 1 轮的历史**（中间空一轮），不会重开新会话 |

也就是说：**人数减少 = 末尾用户提前结束；人数增多 = 新增编号从该轮新开会话；先减后增 = 回归用户续接旧历史**。如果你要「一旦缺席永不回归」，需要在 `generate()` 里加策略，当前默认是上面的语义。

缺席本身对压测有意义：这些用户的 KV 块会被逐步挤出，回归时只能命中 system 段，正好可以观察缓存淘汰行为。

## 场景库 `scenarios.json`

结构是 `{"zh": [...], "en": [...]}`，中文 56 个场景覆盖 33 个领域（数理化生、语文、历史、法律政策、地理、天文、艺术、生活、健康、理财、职场、技术、办公、教学、围棋/篮球/汽车/园艺……），英文 8 个。

单个场景：

```json
{
  "id": "cn_poetry",
  "domain": "语文",
  "style": "explain",
  "subject": "这首唐诗的鉴赏",
  "focus": ["意象选择", "炼字", "情感表达"],
  "entities": ["王维", "边塞", "月亮"],
  "facts": [["字数", "字", 20, 60]],
  "deliverable": "鉴赏思路",
  "who": "语文老师"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 唯一标识 |
| `domain` | 是 | 领域，仅用于描述 |
| `style` | 是 | 对话风格，决定问句句式与回答结构：`diagnose` / `solve` / `explain` / `create` / `plan` / `compare` / `advise` / `review` |
| `subject` | 是 | 话题（填进问句主语） |
| `focus` | 是 | ≥2 个关注点，按轮次轮换，制造多轮递进 |
| `entities` | 是 | ≥2 个实体，按轮次轮换 |
| `facts` | 否 | `[名称, 单位, 下限, 上限]`，有就生成带数值的证据行 |
| `deliverable` | 是 | 第 3 轮要产出的东西（如「故障复盘」） |
| `who` | 是 | 产出给谁看 |

加场景只要往 `zh` 数组里加一条，脚本会自动校验重复 `id`、缺字段、非法 `style`、`facts` 格式。用户与场景的对应关系是「按 `--seed` 打乱后取第 `i` 个」，因此 20 个用户一定拿到 20 个不同场景；单轮人数超过场景数时会复用并打印警告。

## 接到 AISBench

AISBench 的 LongBench 任务走 `load_dataset(path=<LongBench 目录>, name=<任务名>)`，再由目录里的 `LongBench.py` 读取 `data/<任务名>.jsonl`。所以：

1. 把生成的文件放到 `{aisbench}/ais_bench/datasets/LongBench/data/agent_mt.jsonl`；
2. 在 `LongBench.py` 的 `task_list` 里加一行 `"agent_mt"`（否则会报 `BuilderConfig 'agent_mt' not found`）；
3. 复制一份 `configs/datasets/longbench/longbench_2wikimqa/longbench_2wikimqa_gen.py`，把 `abbr` 改为 `agent_mt_gen`、`name` 改为 `'agent_mt'`，prompt 模板保留 `{context}` + `{input}` 即可；
4. 跑 perf：`ais_bench --models <vllm_api 任务> --datasets agent_mt_gen -m perf`。

注意事项：

- 这些配置是**单轮语义**（一行一个请求），多轮是靠 `context` 里带历史实现的，正好匹配「按顺序到达」；
- perf 模式不要开 shuffle / 随机采样，否则前缀命中会乱；
- `dataset` 字段用自定义名字时，**官方 LongBench 的 `eval.py` 会因为 `dataset2metric` 里没有这个 key 而报错**；纯压测不跑精度就没影响。

## 常见报错：`KeyError: "Column answer not in the dataset"`

```
KeyError: "Column answer not in the dataset. Current columns in the dataset:
['input', 'context', 'answers', 'length', 'dataset', 'language', 'all_classes', '_id', 'subdivision', 'idx']"
```

**原因**：这个报错来自 AISBench 的自定义数据集（`--custom-dataset-path`）路径。它默认套用 `custom_qa` 配置：

```python
reader_cfg = dict(input_columns=['question', 'max_out_len'], output_column='answer')
```

而 LongBench v1 的字段是 `input` / `context` / `answers`，两边对不上，`get_gold_ans()` 取 `answer` 列时就炸了（列名里的 `subdivision` / `idx` 是 AISBench 的 `BaseDataset` 自己加的）。

**需要重新生成数据吗**：不需要。数据本身没问题，报错是 AISBench 配置的列映射不对。只有当你想要 v2 字段时，才需要加 `--format v2` 再生成一次（见上一节）。

**三种解法**：

1. **用本仓库的配置（推荐）**：`aisbench/agent_mt_gen.py` 里已经写好了正确的列映射，改一下 `dataset_path` 即可：

   ```bash
   ais_bench --config aisbench/agent_mt_gen.py -m all
   ```

   性能测试的话，把这个文件里的 `datasets = [...]` 块拷进你自己的 perf 配置即可。

2. **走 LongBench 官方配置**：把 jsonl 放到 `ais_bench/datasets/LongBench/data/<name>.jsonl`，在 `LongBench.py` 的 `task_list` 加 `<name>`，再用 `longbench_<name>_gen` 配置（它的 `output_column='answers'`，与本文件格式一致）。

3. **不要**把 LongBench 格式的文件直接喂给 `--custom-dataset-path`，它是按 `question` / `answer` 解析的；即使补上这两个字段，`question` 里也没有你的 `context`，长上下文会被丢掉。

## 兼容性

- 只用标准库，Python 3.8–3.13 均可运行（GitHub Actions 在 3.9 / 3.12 / 3.13 上做冒烟测试）
- 3.11 起 `random.Random` 不再接受 tuple 作为种子，生成器已改用整数种子；3.9 与 3.12 的输出逐字节一致

## 已知限制

- 文本是模板 + 场景库合成的，**通顺但事实是编的**（指标、时间、人名都是随机槽位），不能当知识库或评测集；
- `answers` 只是占位回答，不是标准答案；
- 同 `--seed` 输出完全一致，换 seed 会改变场景分配、数值和措辞；
- 生成器按字符/词计长度，不依赖 tokenizer；要精确 token 数请在 AISBench 或推理框架侧统计；
- 长文档模式引用的文本来自 [LongBench](https://huggingface.co/datasets/zai-org/LongBench)（THUDM/zai-org，AI2D/XLSUM 等子任务各有来源），示例数据集仅作压测用途，二次分发请遵循上游许可；
- 深色/浅色编码、文件编码统一为 UTF-8，`ensure_ascii=False`，可直接 `json.loads` 逐行读取。

## 手工验证

```bash
python3 - <<'EOF'
import json
recs = [json.loads(l) for l in open('datasets/agent_mt_3x20.jsonl', encoding='utf-8')]
keys = {"input","context","answers","length","dataset","language","all_classes","_id"}
assert all(set(r) == keys for r in recs)
by = {}
for r in recs: by.setdefault(r["_id"].split("_")[0], []).append(r)
for items in by.values():
    for p, c in zip(items, items[1:]):
        assert c["context"] == p["context"] + "\n\n" + p["input"] + "\n\n" + p["answers"][0]
print("ok:", len(recs), "lines")
EOF
```
