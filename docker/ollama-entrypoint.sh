#!/bin/sh
set -e

OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"

echo "==> Starting Ollama serve..."
ollama serve &
OLLAMA_PID=$!

echo "==> Waiting for Ollama to be ready..."
until ollama list > /dev/null 2>&1; do
  sleep 2
done
echo "==> Ollama is ready."

if ollama list 2>/dev/null | grep -q "^${OLLAMA_MODEL%%:*}"; then
  echo "==> Model ${OLLAMA_MODEL} already present, skipping pull."
else
  echo "==> Pulling model ${OLLAMA_MODEL} (this may take a while on first run)..."
  ollama pull "$OLLAMA_MODEL"
  echo "==> Model ${OLLAMA_MODEL} pulled successfully."
fi

echo "==> Warming up model ${OLLAMA_MODEL}..."
echo '{"model":"'"$OLLAMA_MODEL"'","messages":[{"role":"user","content":"hi"}],"stream":false}' | timeout 120 wget -q -O- --post-data=- --header='Content-Type: application/json' http://localhost:11434/api/chat 2>/dev/null || true
echo "==> Model warmed up."

echo "==> Ollama is fully ready. Following logs..."
wait $OLLAMA_PID
