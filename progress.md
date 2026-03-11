# Project Progress Log

**Date:** 2026-03-11

## Current State (Iteration 2)
The Sound-Vision Assistive Workflow is currently a tightly-integrated, locally-hosted AI assistive application designed for real-time scene understanding and audio feedback.

Key features currently implemented and working:
- **Architecture:** Fully containerized using Docker Compose with `uv` for lightning-fast Python dependency management.
- **Local AI Engine:** Integrated a Vision-Language Model (`llama3.2-vision`) via Ollama as the primary engine for semantic scene understanding, replacing the basic bounding-box geometry of the legacy YOLO engine (which remains as a fallback option).
- **Self-Contained Containerization:** Ollama runs as a dedicated, GPU-accelerated background service within the Docker network. Included a custom startup script (`ollama-entrypoint.sh`) that safely pauses the Python app and pulls the 7.8GB model automatically on first boot.
- **Asynchronous Processing:** The heavy VLM inference runs in a non-blocking background thread. This allows the application to ingest video without stuttering or freezing.
- **Advanced Telemetry & UI Debugger:** Built a robust visual debugging window featuring a split-screen UI:
  - **Left (Live Feed):** Smooth 30 FPS video with dynamic red/green borders indicating when the AI is busy vs. when it actively grabs a frame for analysis.
  - **Right (AI View):** A frozen snapshot of the exact frame the VLM is currently "thinking" about.
  - **Telemetry Overlay:** Real-time overlaid text showing the AI's exact text output and its processing latency (in seconds).
- **Hardware Passthrough:** Successfully configured Docker to securely pass through `/dev/video0` (webcam) and PulseAudio streams so the containerized app can see the world and speak to the Linux host using `pyttsx3`.

## Future Scopes
- **Cloud VLM Integration:** Fully test the `VLMEngine`'s ability to seamlessly swap to cloud-based VLMs (e.g., OpenRouter API) for scenarios where local hardware isn't powerful enough or a smarter model is needed.
- **Accuracy & Prompt Engineering:** Continuously refine the VLM prompts and test different models to improve the functional accuracy of the descriptions for visually impaired users.
- **Agentic Analysis (CrewAI):** Introduce a secondary AI layer or Agent workflow to analyze the VLM's raw output, filter out hallucinations, and generate more context-aware navigational feedback.
- **Production Deployment (Headless):** Transition from the OpenCV visual debugging window to a completely headless, audio-only mode optimized for deployment on edge devices like a Raspberry Pi or NVIDIA Jetson.
