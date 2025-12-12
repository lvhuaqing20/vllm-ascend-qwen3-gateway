#!/usr/bin/env bash
set -euo pipefail

IMAGE="quay.io/ascend/vllm-ascend:v0.10.0rc1-310p"
CONTAINER="vllm_core"

# 默认使用 0 号 NPU；如果你想用 1 号卡：ASCEND_VISIBLE_DEVICES=1 ./scripts/run_backend.sh
ASCEND_VISIBLE_DEVICES="${ASCEND_VISIBLE_DEVICES:-0}"

# ModelScope 缓存（放在毕业设计目录内，便于复现与写文档）
MS_CACHE_DIR="$(cd "$(dirname "$0")/.." && pwd)/model_cache/modelscope"

echo "[INFO] Using IMAGE=${IMAGE}"
echo "[INFO] Using CONTAINER=${CONTAINER}"
echo "[INFO] ASCEND_VISIBLE_DEVICES=${ASCEND_VISIBLE_DEVICES}"
echo "[INFO] ModelScope cache dir: ${MS_CACHE_DIR}"

# 如果同名容器已存在，先删掉（避免端口占用/配置冲突）
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "[INFO] Removing existing container ${CONTAINER} ..."
  docker rm -f "${CONTAINER}" >/dev/null
fi

docker run -itd --name "${CONTAINER}" \
  --net=host \
  --ipc=host \
  --privileged \
  -v /usr/local/Ascend:/usr/local/Ascend \
  -v /home/leijianuo/Ascend/nnal:/usr/local/Ascend/nnal \
  -v /home/leijianuo/Ascend/ascend-toolkit:/usr/local/Ascend/ascend-toolkit \
  -v /dev:/dev \
  -v /home/leijianuo/Ascend:/home/leijianuo/Ascend \
  -v "${MS_CACHE_DIR}:/root/.cache/modelscope" \
  -e ASCEND_VISIBLE_DEVICES="${ASCEND_VISIBLE_DEVICES}" \
  -e VLLM_USE_MODELSCOPE=true \
  "${IMAGE}" \
  python -m vllm.entrypoints.openai.api_server \
    --host 0.0.0.0 \
    --port 8000 \
    --model Qwen/Qwen3-0.6B \
    --served-model-name Qwen3-0.6B \
    --trust-remote-code \
    --dtype float16 \
    --max-model-len 8192 \
    --enforce-eager

echo "[INFO] Started. Tailing logs..."
docker logs -f "${CONTAINER}"
