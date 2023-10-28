import base64
import requests
import os


class Stable:
    def __init__(self):
        # self.url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image" #stable 1
        # self.url = "https://api.stability.ai/v1/generation/stable-diffusion-v1-5/text-to-image" # stable 1.5
        self.url = "https://api.stability.ai/v1/generation/stable-diffusion-512-v2-1/text-to-image"  # stable 2

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-f0nm5eii4k4yJlSEx7O6ufUidnLq3AzhNAOFC6qpvMnF4cxA",
        }

    def generate_image(self, prompt):
        self.prompt = prompt
        body = {
            "steps": 10,
            "width": 512,
            "height": 512,
            "seed": 0,
            "cfg_scale": 5,
            "samples": 1,
            "text_prompts": [
                {"text": self.prompt, "weight": 1},
                {"text": "blurry, bad", "weight": -1},
            ],
        }

        response = requests.post(self.url, headers=self.headers, json=body)

        if response.status_code != 200:
            raise Exception("Non-200 response: " + str(response.text))

        data = response.json()

        # make sure the out directory exists
        if not os.path.exists("./static/images"):
            os.makedirs("./static/images")

        for i, image in enumerate(data["artifacts"]):
            with open(f'./static/images/txt2img_{image["seed"]}.png', "wb") as f:
                f.write(base64.b64decode(image["base64"]))

            return f'./static/images/txt2img_{image["seed"]}.png', image["seed"]
