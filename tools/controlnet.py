import requests
import json
from io import BytesIO
from PIL import Image
import os

class ControlNet:
    def __init__(self, api):
        self.api = api

    def make_api_request(self, prompt, image_path):
        url = "https://stablediffusionapi.com/api/v5/controlnet"
        payload = {
            "key": self.api,
            "controlnet_model": "canny",
            "controlnet_type": "canny",
            "model_id": "midjourney",
            "auto_hint": "yes",
            "guess_mode": "no",
            "prompt": self.prompt,
            "negative_prompt": None,
            "init_image": self.image_path,
            "mask_image": None,
            "width": "512",
            "height": "512",
            "samples": "1",
            "scheduler": "UniPCMultistepScheduler",
            "num_inference_steps": "30",
            "safety_checker": "no",
            "enhance_prompt": "yes",
            "guidance_scale": 7.5,
            "strength": 0.55,
            "lora_model": None,
            "tomesd": "yes",
            "use_karras_sigmas": "yes",
            "vae": None,
            "lora_strength": None,
            "embeddings_model": None,
            "seed": None,
            "webhook": None,
            "track_id": None
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        return response

    @staticmethod
    def save_image(image_bytes, seed):
        if not os.path.exists("./static/images"):
            os.makedirs("./static/images")

        with open(f'./static/images/img2img_{seed}.png', "wb") as f:
            f.write(image_bytes.getvalue())

        return f'./static/images/img2img_{seed}.png', seed

    def extract_image_from_response(self, response):
        if response["status"] == "success" and "output" in response and len(response["output"]) > 0:
            image_url = response["output"][0]
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                image_bytes = BytesIO(image_response.content)
                image = Image.open(image_bytes)

                seed = response["meta"]["seed"]
                saved_image_path, seed = self.save_image(image_bytes, seed)

                return saved_image_path, seed
            else:
                print(f"Failed to retrieve image. Status code: {image_response.status_code}")
        else:
            print("Invalid API response or no image found.")

    def process_request(self, prompt, image_path):
        response = self.make_api_request(prompt, image_path)

        if response.status_code == 200:
            api_response = response.json()
            saved_image_path, seed = self.extract_image_from_response(api_response)

            if saved_image_path:
                print(f"Image saved at: {saved_image_path}")
                print(f"Seed: {seed}")
            else:
                print("Failed to save image.")
        else:
            print(f"Failed to make API request. Status code: {response.status_code}")


# Example usage

api_key = "o4GCZ0DZox648YizgwbnvmiFTvpb4D7bbbTqx7gd0vLre7WJmMad4jBFmjLN"
prompt_text = "mountains and river, ultra high resolution, 4K image"
image_url = "https://storage.googleapis.com/rimorai_bucket1/horse/txt2img_86571881.png"

extractor = ControlNet(api_key)
extractor.process_request(prompt_text, image_url)