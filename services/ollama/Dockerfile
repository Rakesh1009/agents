FROM ollama/ollama:latest

# Copy our custom entrypoint script into the image
COPY ollama-entrypoint.sh /ollama-entrypoint.sh
RUN chmod +x /ollama-entrypoint.sh

# Use our script to start the server and pull the model
ENTRYPOINT ["/bin/bash", "/ollama-entrypoint.sh"]
