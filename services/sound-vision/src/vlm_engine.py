import os
import base64
import cv2
from openai import OpenAI

# Default system prompt designed to extract highly focused spatial/actionable data
DEFAULT_PROMPT = """
Describe the scene in front of you in one short, functional sentence. 
Focus only on the most prominent objects, people, or obstacles. 
Do not try to identify individuals. Do not describe image quality. 
Just state what is physically there (e.g., "A person wearing an orange shirt is standing in front of a white wall.").
"""

class VLMEngine:
    """Handles interaction with an OpenAI-compatible Vision Language Model API."""
    
    def __init__(self, endpoint_type="auto"):
        """
        Initializes the VLM client.
        Supports pointing to a local host (Ollama) or a cloud provider (OpenRouter).
        """
        # Try to infer configuration from environment variables if not strictly specified
        self.api_key = os.getenv("VLM_API_KEY", "dummy-key-for-local")
        self.base_url = os.getenv("VLM_BASE_URL")
        self.model = os.getenv("VLM_MODEL", "llama3.2-vision")
        
        # Determine the endpoint type if 'auto'
        if endpoint_type == "auto":
            if "openrouter" in str(self.base_url).lower():
                endpoint_type = "openrouter"
            else:
                # Default to local ollama endpoint if nothing else makes sense
                endpoint_type = "local"
                if not self.base_url:
                    # In docker, 'host.docker.internal' often points to the host machine running Ollama
                    self.base_url = "http://host.docker.internal:11434/v1"
        
        print(f"Initializing VLM Engine [{endpoint_type.upper()}]")
        print(f"  URL: {self.base_url}")
        print(f"  Model: {self.model}")
        
        # Standard OpenAI client works for Ollama (v1), vLLM, OpenAI, and OpenRouter
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def _encode_image(self, frame):
        """Converts an OpenCV BGR frame to a base64 encoded JPEG string."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Compress to JPEG to save bandwidth/API token limits
        # Increased to 90 quality because small VLMs struggle with compression artifacts
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        success, buffer = cv2.imencode('.jpg', rgb_frame, encode_param)
        
        if not success:
            raise ValueError("Could not encode frame to JPEG")
            
        return base64.b64encode(buffer).decode('utf-8')

    def is_model_ready(self):
        """
        Pings the VLM model to check if it's awake and completely downloaded.
        Returns True if the model successfully responds to a basic prompt, False otherwise.
        """
        try:
            # We don't send an image, just a tiny text prompt to verify it's loaded
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            # Catch 404 (model downloading) or Connection Error (server off)
            return False

    def analyze_frame(self, frame, prompt=DEFAULT_PROMPT):
        """
        Sends the frame to the VLM and returns the generated descriptive text.
        """
        try:
            base64_image = self._encode_image(frame)
            
            # Construct the payload according to the OpenAI Vision API standard
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=50, # Keep it extremely short and snappy
                temperature=0.2 # low temperature = more deterministic, less creative rambling
            )
            
            # Extract the actual text response
            output_text = response.choices[0].message.content.strip()
            return output_text
            
        except Exception as e:
            print(f"[VLM ERROR] {e}")
            return "Vision processing error."
