#!/bin/bash

ollama serve &
OLLAMA_SERVER_PID=$!

echo 'Waiting for Ollama server to be ready...'
until curl -f http://localhost:11434 > /dev/null 2>&1; do
  sleep 1;
done;
echo 'Ollama server is ready.'

MODEL_TO_PULL='llama3.2:1b'

if ! ollama list | grep -q ${MODEL_TO_PULL}; then
  echo "Pulling model: ${MODEL_TO_PULL}"
  ollama pull ${MODEL_TO_PULL}
  if [ $? -ne 0 ]; then
    echo "Error: Failed to pull model ${MODEL_TO_PULL}. Exiting."
    kill $OLLAMA_SERVER_PID
    exit 1
  fi
  echo "Model ${MODEL_TO_PULL} pulled successfully."
else
  echo "Model ${MODEL_TO_PULL} already exists."
fi;

wait $OLLAMA_SERVER_PID