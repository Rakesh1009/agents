#!/bin/bash
# ollama-entrypoint.sh 
# Custom lightweight entrypoint to ensure the required model is pulled on startup.

# Start the actual Ollama daemon in the background
/bin/ollama serve &
# Record the Process ID of the server so we can listen to it
pid=$!

echo "Waiting for Ollama API to wake up..."
# Wait up to 15 seconds for the API to respond
sleep 3

echo "Ollama is awake. Pulling llama3.2-vision model (this may take a while the first time)..."
# Pull the model. If it already exists in the volume, this is nearly instantaneous.
ollama pull llama3.2-vision

echo "Model is ready. Keeping server alive."
# Wait for the background `ollama serve` process to exit
wait $pid
