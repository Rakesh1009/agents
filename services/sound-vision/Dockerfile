# Use Ubuntu 24.04 (Noble Numbat) as the base image
FROM ubuntu:24.04

# Maintainer info
LABEL maintainer="Sound-Vision Assistive Workflow"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for video (OpenCV) and audio (pyttsx3/PulseAudio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    build-essential \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    # Audio/pyttsx3 dependencies
    espeak-ng \
    alsa-utils \
    pulseaudio \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary directly from the official image for reliability
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create app directory
WORKDIR /app

# Copy dependency requirements first to leverage Docker cache
COPY requirements.txt .

# Create a virtual environment and install dependencies using uv
# We use --system to install directly in the container or we can use virtual env.
# uv is very fast, let's use a virtual environment for best practices.
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN uv pip install -r requirements.txt

# Copy the rest of the application
COPY . /app

# Ensure we have rights to video and audio devices (often handled by run script, but good practice)
# Set the entrypoint to our main script
CMD ["python", "src/main.py"]
