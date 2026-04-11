import json
import os
import fal_client
from crewai.tools import tool


@tool("generate_illustration")
def generate_illustration(prompt: str) -> str:
    """Generate a scientific illustration using fal.ai and return the image URL."""
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        return json.dumps({"error": "FAL_KEY environment variable is not set"})

    fal_model = os.getenv("FAL_MODEL")
    if not fal_model:
        return json.dumps({"error": "FAL_MODEL environment variable is not set"})

    try:
        result = fal_client.subscribe(
            fal_model,
            arguments={
                "prompt": prompt,
                "image_size": "landscape_16_9",
                "num_inference_steps": 40,
                "guidance_scale": 3.5,
            },
        )
        if result and result.get("images"):
            url = result["images"][0]["url"]
            return f"Illustration generated: {url}"
        return json.dumps({"error": "Image generation failed."})
    except Exception as e:
        return json.dumps({"error": f"Image generation error: {e}"})
