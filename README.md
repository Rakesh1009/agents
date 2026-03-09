# Sound-Vision Assistive Workflow

## Project Statement
> "An MCP-based assistive workflow that leverages multimodal AI to translate live video feeds into real-time audio cues, empowering visually impaired individuals to perceive and navigate their environment entirely through sound."

## Description
This project is an MCP-driven assistive workflow that processes live video feeds using a multimodal AI model (local or server-hosted) and translates the visual data strictly into real-time audio cues. By eliminating visual outputs and focusing entirely on sound-vision linking, the system extracts critical environmental information—such as object proximity, spatial layout, and text—and delivers it through auditory feedback, providing visually impaired users with continuous spatial awareness.

## Core Architecture & Tech Stack
* **Workflow Engine:** Model Context Protocol (MCP) to manage the pipeline between inputs, AI processing, and outputs.
* **Input:** Real-time video/camera feeds.
* **Processing Engine:** Multimodal AI model. Designed to be flexible, supporting either a lightweight local model (for speed/privacy) or a server-hosted model (for complex inference).
* **Output:** Strictly audio cues. No visual interface required for the end-user. 



## Implementation Strategy & Data Flow

### 1. Ingestion and Pre-processing (The Eye)
The system captures live video from the user's device (e.g., smart glasses, smartphone camera). To ensure low latency, the feed is downsampled into discrete, high-information keyframes rather than processing a continuous 60fps stream. These frames are temporarily buffered and formatted into base64 payloads.

### 2. MCP Orchestration (The Brain Stem)
The Model Context Protocol acts as the bridge. An MCP server is instantiated to receive the frame payloads and system prompts. It determines routing based on current connectivity and battery life:
* **Offline/Low-Latency Mode:** Routes the payload to a lightweight local multimodal model (e.g., a quantized vision-language model).
* **High-Fidelity Mode:** Routes to a server-hosted model via API for dense scene analysis (e.g., reading complex signage or identifying specific faces).

### 3. Multimodal Inference (The Visual Cortex)
The AI model processes the frames against a strict system prompt designed for accessibility. It is instructed to ignore aesthetic details and focus entirely on actionable data:
* Obstacle detection and proximity.
* Scene context (e.g., "crosswalk ahead," "approaching stairs").
* Text extraction (OCR).
The output is generated as a structured JSON response containing priority tags (Urgent, Informational, Ambient) and concise descriptive text.

### 4. Audio Cue Synthesis (The Voice)
The structured text output is passed to an audio rendering engine. 
* **Urgent Data (e.g., immediate obstacles):** Mapped to distinct, non-verbal spatial audio tones (beeps or haptic-like sounds).
* **Informational Data (e.g., reading a sign):** Processed through a high-speed Text-to-Speech (TTS) engine.
This output is piped directly to the user's earpiece, providing a continuous, prioritized stream of auditory environmental awareness.

## PS: This is just a plan for now, It will be developed sequentially
First iteration will be trying to say use a yolo model and detect person and convert that data into audio.