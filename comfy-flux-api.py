import os
import uuid
import json
import random
import websocket
import urllib.request
from typing import Dict, List, Optional, Tuple, Union

class ComfyFluxAPI:
    def __init__(self, server_address: str = "127.0.0.1:8188"):
        """Initialize the ComfyUI Flux API client.
        
        Args:
            server_address: The address of the ComfyUI server (default: "127.0.0.1:8188")
        """
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.workflow = self._load_base_workflow()
        
    def _load_base_workflow(self) -> Dict:
        """Load the base workflow configuration."""
        base_workflow = {
            "6": {  # CLIPTextEncode (Positive Prompt)
                "inputs": {
                    "clip": ["11", 0],
                    "text": ""
                },
                "class_type": "CLIPTextEncode"
            },
            "10": {  # VAELoader
                "inputs": {
                    "vae_name": "ae.safetensors"
                },
                "class_type": "VAELoader"
            },
            "11": {  # DualCLIPLoader
                "inputs": {
                    "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
                    "clip_name2": "clip_l.safetensors",
                    "mode": "flux"
                },
                "class_type": "DualCLIPLoader"
            },
            "42": {  # UnetLoaderGGUF
                "inputs": {
                    "model_name": "flux1-dev-Q4_0.gguf"
                },
                "class_type": "UnetLoaderGGUF"
            }
        }
        return base_workflow

    def _open_websocket(self) -> websocket.WebSocket:
        """Create and return a websocket connection."""
        ws = websocket.WebSocket()
        ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
        return ws

    def _queue_prompt(self, prompt: Dict) -> Dict:
        """Queue a prompt for processing.
        
        Args:
            prompt: The prompt configuration
            
        Returns:
            Dict containing the response from the server
        """
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(
            f"http://{self.server_address}/prompt",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        return json.loads(urllib.request.urlopen(req).read())

    def _get_image_urls(self, prompt_id: str) -> List[str]:
        """Get the URLs of generated images.
        
        Args:
            prompt_id: The ID of the prompt
            
        Returns:
            List of image URLs
        """
        with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
            history = json.loads(response.read())
            
        image_urls = []
        outputs = history[prompt_id]["outputs"]
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for image in node_output["images"]:
                    if image["type"] == "output":
                        url = f"http://{self.server_address}/view?filename={image['filename']}&subfolder={image['subfolder']}&type={image['type']}"
                        image_urls.append(url)
        return image_urls

    def _track_progress(self, ws: websocket.WebSocket, prompt_id: str) -> None:
        """Track the progress of image generation.
        
        Args:
            ws: WebSocket connection
            prompt_id: The ID of the prompt
        """
        while True:
            try:
                msg = ws.recv()
                if isinstance(msg, str):
                    message = json.loads(msg)
                    if message["type"] == "progress":
                        print(f'Progress: Step {message["data"]["value"]} of {message["data"]["max"]}')
                    elif message["type"] == "execution_complete" and message["data"]["prompt_id"] == prompt_id:
                        break
            except websocket.WebSocketConnectionClosedException:
                break

    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        steps: int = 20,
        cfg_scale: float = 3.5,
        sampler: str = "euler"
    ) -> List[str]:
        """Generate an image using the Flux workflow.
        
        Args:
            prompt: The text prompt for image generation
            width: Image width (default: 1024)
            height: Image height (default: 1024)
            seed: Random seed (default: None, will generate random seed)
            steps: Number of sampling steps (default: 20)
            cfg_scale: Classifier-free guidance scale (default: 3.5)
            sampler: Sampling algorithm (default: "euler")
            
        Returns:
            List of URLs for the generated images
        """
        if seed is None:
            seed = random.randint(0, 0xffffffffffffffff)

        # Update workflow with parameters
        workflow = self.workflow.copy()
        
        # Set prompt
        workflow["6"]["inputs"]["text"] = prompt
        
        # Set dimensions
        workflow["27"] = {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptySD3LatentImage"
        }
        
        # Set sampler settings
        workflow["17"] = {
            "inputs": {
                "scheduler": "simple",
                "steps": steps,
                "denoise": 1
            },
            "class_type": "BasicScheduler"
        }
        
        workflow["16"] = {
            "inputs": {
                "sampler_name": sampler
            },
            "class_type": "KSamplerSelect"
        }
        
        workflow["26"] = {
            "inputs": {
                "value": cfg_scale
            },
            "class_type": "FluxGuidance"
        }
        
        # Set random seed
        workflow["25"] = {
            "inputs": {
                "seed": seed
            },
            "class_type": "RandomNoise"
        }

        # Connect nodes
        self._add_connections(workflow)

        # Generate image
        ws = self._open_websocket()
        try:
            response = self._queue_prompt(workflow)
            prompt_id = response["prompt_id"]
            self._track_progress(ws, prompt_id)
            return self._get_image_urls(prompt_id)
        finally:
            ws.close()

    def _add_connections(self, workflow: Dict) -> None:
        """Add necessary connections between nodes in the workflow."""
        workflow.update({
            "connections": [
                ["6", "26", "CONDITIONING"],  # CLIP Text Encode -> Flux Guidance
                ["26", "22", "CONDITIONING"],  # Flux Guidance -> Basic Guider
                ["42", "30", "MODEL"],        # UNET -> Model Sampling Flux
                ["30", "22", "MODEL"],        # Model Sampling -> Basic Guider
                ["30", "17", "MODEL"],        # Model Sampling -> Basic Scheduler
                ["17", "13", "SIGMAS"],       # Basic Scheduler -> Sampler
                ["16", "13", "SAMPLER"],      # KSampler Select -> Sampler
                ["25", "13", "NOISE"],        # Random Noise -> Sampler
                ["27", "13", "LATENT"],       # Empty Latent -> Sampler
                ["13", "8", "LATENT"],        # Sampler -> VAE Decode
                ["10", "8", "VAE"],           # VAE Loader -> VAE Decode
                ["8", "9", "IMAGE"]           # VAE Decode -> Save Image
            ]
        })

# Example usage
if __name__ == "__main__":
    api = ComfyFluxAPI()
    
    # Generate a simple image
    urls = api.generate_image(
        prompt="A cute cat sitting in a garden",
        width=1024,
        height=1024,
        steps=20,
        cfg_scale=3.5,
        sampler="euler"
    )
    
    print("Generated image URLs:", urls)
