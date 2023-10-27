import base64
import requests
import os


class Stable:
    def __init__(self):
        self.url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-lP8Czt6S8TOvEPbdkesem8uaw0gbvoX2eMbOrxkx512iIRHn",
        }

    def generate_image(self, prompt):
        self.prompt = prompt
        body = {
            "steps": 20,
            "width": 896,
            "height": 1152,
            "seed": 0,
            "cfg_scale": 3,
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
