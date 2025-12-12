import uvicorn
from fastapi import FastAPI, Request, HTTPException
import httpx
import re

app = FastAPI(title="Qwen3 Fast/Slow Gateway")

# vLLM 后端地址
VLLM_URL = "http://127.0.0.1:8000/v1/chat/completions"

# slow 模式 system prompt（引导深度推理）
SLOW_SYSTEM_PROMPT = """你是一个具备深度推理能力的 AI 助手。
请在回答问题前进行充分、完整的逻辑分析，并在最后给出结论。
"""

# 仅用于 fast：删除 <think> / <thinking>
THINKING_REGEX = re.compile(
    r"<think>.*?</think>|<thinking>.*?</thinking>",
    re.DOTALL | re.IGNORECASE
)


def strip_thinking(text: str) -> str:
    if not text:
        return text
    return THINKING_REGEX.sub("", text).strip()


@app.post("/v1/chat/completions")
async def proxy_chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 1️⃣ 读取 mode（默认 fast）
    mode = body.pop("mode", "fast")
    messages = body.get("messages", [])

    # 2️⃣ 参数与 prompt 控制
    if mode == "slow":
        print("⚡ [Mode: SLOW] keep reasoning output")

        body["temperature"] = body.get("temperature", 0.6)
        body["max_tokens"] = body.get("max_tokens", 1024)

        # 注入 system prompt（只影响 slow）
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] = (
                SLOW_SYSTEM_PROMPT + "\n" + messages[0]["content"]
            )
        else:
            messages.insert(
                0, {"role": "system", "content": SLOW_SYSTEM_PROMPT}
            )

    else:
        print("🚀 [Mode: FAST] strip reasoning")

        body["temperature"] = body.get("temperature", 0.1)
        body["max_tokens"] = body.get("max_tokens", 256)

    body["messages"] = messages

    # 3️⃣ 转发给 vLLM
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(VLLM_URL, json=body)

    if resp.status_code != 200:
        return resp.json()

    data = resp.json()

    # 4️⃣ 关键区别：只在 fast 模式清洗推理
    if mode == "fast":
        try:
            content = data["choices"][0]["message"]["content"]
            data["choices"][0]["message"]["content"] = strip_thinking(content)
        except Exception:
            pass

    return data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

