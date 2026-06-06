import base64
import json
import os
from datetime import datetime

from openai import OpenAI
from crewai.tools import tool


@tool("generate_illustration")
def generate_illustration(prompt: str) -> str:
    """Generate a scientific illustration using MeliousAI and return the local file path."""
    api_key = os.getenv("MELIOUS_API_KEY")
    if not api_key:
        return json.dumps({"error": "MELIOUS_API_KEY environment variable is not set"})

    base_url = os.getenv("MELIOUS_BASE_URL")
    if not base_url:
        return json.dumps({"error": "MELIOUS_BASE_URL environment variable is not set"})

    image_model = os.getenv("MELIOUS_IMAGE_MODEL")
    if not image_model:
        return json.dumps({"error": "MELIOUS_IMAGE_MODEL environment variable is not set"})

    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=120)
        response = client.images.generate(
            model=image_model,
            prompt=prompt,
            size="1792x1024",
        )
        if response.data and response.data[0].b64_json:
            image_data = base64.b64decode(response.data[0].b64_json)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"output/illustration_{timestamp}.png"
            os.makedirs("output", exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(image_data)
            return f"Illustration saved: {filepath}"
        return json.dumps({"error": "Image generation failed — no base64 data returned."})
    except Exception as e:
        return json.dumps({"error": f"Image generation error: {e}"})
