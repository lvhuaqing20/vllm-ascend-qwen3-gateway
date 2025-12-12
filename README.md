# vLLM-Ascend Qwen3 Gateway

## 一、项目简介

本项目是一个基于 **华为昇腾（Ascend）NPU** 的大语言模型推理系统，使用 **vLLM-Ascend** 框架部署 **Qwen3-0.6B** 模型，并在其上实现了一个轻量级 **HTTP Gateway（网关服务）**。

项目支持两种推理模式：

- **Fast 模式**：仅返回最终答案，不包含推理过程，适用于高吞吐、低延迟场景  
- **Slow 模式**：返回包含完整推理过程的回答，适用于调试、教学与分析场景  

该项目作为毕业设计的一部分，重点展示了：

- 昇腾 NPU 上的大模型推理部署流程  
- vLLM 在 Ascend 平台上的使用方式  
- 推理服务的工程化封装（API Gateway）  
- 不同推理策略在工程层面的取舍与实现  

---

## 二、系统与环境要求

### 1. 硬件环境

- 华为昇腾 **Atlas 300I Duo**  
- 架构：`x86_64`

### 2. 软件环境

- 操作系统：Linux（推荐 Ubuntu 20.04 / 22.04）
- CANN：**8.2 RC1**
- Python：**3.11+**
- Docker（用于运行 vLLM-Ascend 镜像）
- vLLM-Ascend 镜像：`quay.io/ascend/vllm-ascend:v0.10.0rc1-310p`

---

## 三、项目目录结构说明

```
vllm-ascend-qwen3/
├── gateway/                    # 推理网关服务
│   └── proxy_server.py         # Fast / Slow 模式逻辑
├── scripts/
│   └── run_backend.sh          # vLLM-Ascend 后端启动脚本
├── tests/
│   ├── vllm_models.json        # /v1/models 接口示例输出
│   └── vllm_chat_sample.json   # Chat 接口示例输出
├── model_cache/                # 模型缓存（不会提交到 GitHub）
├── .gitignore
└── README.md
```

### 目录说明

- `gateway/`  
  包含 HTTP 网关代码，对外提供 `/v1/chat/completions` 接口，并在内部区分 fast / slow 推理模式。

- `scripts/`  
  包含启动 vLLM-Ascend 后端的脚本，负责 Docker 启动、设备挂载、环境变量配置等。

- `tests/`  
  保存真实接口调用结果，作为可复现的测试样例，方便毕业设计答辩展示。

- `model_cache/`  
  存放模型权重与 tokenizer 文件，**不纳入版本管理**。

---

## 四、运行步骤

### 1. 启动 vLLM-Ascend 后端服务

```bash
cd scripts
./run_backend.sh
```

成功启动后，vLLM API 会监听在：

```
http://127.0.0.1:8000
```

你可以通过以下命令验证：

```bash
curl http://127.0.0.1:8000/v1/models
```

### 2. 启动 Gateway 网关服务

```bash
cd gateway
python3 proxy_server.py
```

网关服务默认监听在：

```
http://127.0.0.1:8080
```

---

## 五、接口使用示例

### 1. Fast 模式（无推理过程，仅答案）

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "fast",
    "model": "Qwen3-0.6B",
    "messages": [
      {"role":"user","content":"请用一句话回答：1+1 等于几？"}
    ],
    "temperature": 0.0,
    "max_tokens": 128
  }' | python3 -c 'import sys,json; print(json.load(sys.stdin)["choices"][0]["message"]["content"])'
```

输出示例：

```
2
```

### 2. Slow 模式（包含推理过程）

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "slow",
    "model": "Qwen3-0.6B",
    "messages": [
      {"role":"user","content":"请解释为什么 1+1=2，并给出一个生活中的例子。"}
    ],
    "max_tokens": 1024
  }'
```

---

## 六、设计说明（毕业设计重点）

### 1. Fast / Slow 模式设计思想

| 模式 | 特点 | 使用场景 |
|------|------|----------|
| Fast | 不输出推理过程，仅保留最终答案 | 实际部署、在线服务 |
| Slow | 输出完整推理过程 | 教学、调试、分析 |

### 2. 工程取舍说明

- Fast 模式通过 系统提示词 + 后处理 抑制推理内容
- Slow 模式保留模型完整输出，便于观察模型内部行为
- Gateway 与模型解耦，便于后续替换模型或增加策略

---

## 七、常见问题

### 1. HuggingFace / ModelScope 下载慢

项目默认使用 ModelScope，模型会缓存在：

```
model_cache/
```

该目录已被 .gitignore 排除。

### 2. NPU Graph 报错

如遇到 NPUGraph.cpp 相关错误，可在后端禁用编译模式，使用 eager 方式运行。

---

## 八、版本管理说明

- 模型权重、缓存、编译产物均不会上传 GitHub
- 仓库中仅包含 源码、脚本、测试样例与文档
- 符合毕业设计代码提交与答辩展示要求

---

## 九、作者信息

- 作者：XXX（你的名字）
- 学校 / 学院：XXX
- 专业：XXX
- 毕业设计题目：基于昇腾 NPU 的大语言模型推理系统设计与实现

---

## 十、License

本项目仅用于学习与毕业设计展示，未用于商业用途。
