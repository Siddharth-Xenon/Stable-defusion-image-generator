import requests
import json
from io import BytesIO
from PIL import Image
import os
import time

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
            "prompt": prompt,
            "negative_prompt": None,
            "init_image": image_path,
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

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  # Raise HTTPError for bad response (4xx and 5xx)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None

    @staticmethod
    def save_image(image_bytes, seed):
        if not os.path.exists("./static/images"):
            os.makedirs("./static/images")

        try:
            with open(f'./static/images/img2img_{seed}.png', "wb") as f:
                f.write(image_bytes.getvalue())
            return f'./static/images/img2img_{seed}.png', seed
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None

    def extract_image_from_response(self, response):
        try:
            if response and response["status"] == "success" and "output" in response and len(response["output"]) > 0:
                image_url = response["output"][0]
                image_response = requests.get(image_url)
                image_response.raise_for_status()  # Raise HTTPError for bad response (4xx and 5xx)
                if image_response.status_code == 200:
                    image_bytes = BytesIO(image_response.content)
                    image = Image.open(image_bytes)

                    seed = response["meta"]["seed"]
                    saved_image_path, seed = self.save_image(image_bytes, seed)

                    return saved_image_path, seed
                else:
                    print(f"Failed to retrieve image. Status code: {image_response.status_code}")
            else:
                print("Invalid API response or no image found.", response)
        except Exception as e:
            print(f"Error extracting image from response: {e}")

    def process_request(self, prompt, image_path):
        response = self.make_api_request(prompt, image_path)
        time.sleep(4)
        if response is not None and response.status_code == 200:
            api_response = response.json()
            saved_image_path, seed = self.extract_image_from_response(api_response)

            if saved_image_path:
                print(f"Image saved at: {saved_image_path}")
                print(f"Seed: {seed}")
            else:
                print("Failed to save image.")
        elif response is not None:
            print(f"Failed to make API request. Status code: {response.status_code}")
        else:
            print("No response received.")
        return saved_image_path, seed

# Example usage
# api_key = "dPUaQdPuy24XCdSnWS9Bkqhz1V6GKo8HygYcTMnj8vLF3hKPr5bdOU6O3LD2"
# prompt_text = "indian cricket player navjyot singh siddhu"
# image_url = "https://storage.googleapis.com/rimorai_bucket1/%23OutlineImages/c83fbd25-b885-4f01-bc55-561ccb0b4e7c_Capture.JPG"

# extractor = ControlNet(api_key)
# extractor.process_request(prompt_text, image_url)