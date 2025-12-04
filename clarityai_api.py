# import os
# import json
# import requests
# import numpy as np
# from PIL import Image
# from io import BytesIO

# class CrystalUpscaler:
#     @classmethod
#     def INPUT_TYPES(s):
#         return {
#             "required": {
#                 "image": ("IMAGE",),
#                 "scale_factor": ("INT", {"default": 2, "min": 1, "max": 200}),
#                 "creativity": ("INT", {"default": 0, "min": 0, "max": 10}),
#             },
#             "optional": {
#                 "api_key_override": ("STRING", {"default": ""}),
#             }
#         }

#     RETURN_TYPES = ("IMAGE",)
#     FUNCTION = "go"
#     CATEGORY = "CrystalAI"

#     def go(self, image, scale_factor, creativity, api_key_override):

#         # API key resolution
#         api_key = api_key_override.strip() or os.getenv("CRYSTAL_API_KEY", "")
#         if not api_key:
#             raise Exception("Missing API key: supply override or set CRYSTAL_API_KEY env var.")

#         # Convert ComfyUI tensor to a PNG file buffer
#         pil = Image.fromarray((image[0].cpu().numpy() * 255).astype(np.uint8))
#         buf = BytesIO()
#         pil.save(buf, format="PNG")
#         img_bytes = buf.getvalue()

#         # ------------------------------------------------------------------
#         # STEP 1 — Upload to your private host
#         # ------------------------------------------------------------------
#         upload_url = "https://ace.genfrontai.com:3000/put_crystal"
#         r = requests.post(
#             upload_url,
#             files={"file": ("input.png", img_bytes, "image/png")},
#             timeout=60
#         )

#         if r.status_code != 200:
#             raise Exception(f"Upload failed: {r.text}")

#         image_url = r.json()["url"]

#         # ------------------------------------------------------------------
#         # STEP 2 — Send URL to Crystal
#         # ------------------------------------------------------------------
#         payload = {
#             "mode": "crystal",
#             "image": image_url,
#             "scale_factor": scale_factor,
#             "creativity": creativity,
#             "output_format": "png"
#         }

#         cr = requests.post(
#             "https://api-upscale.clarityai.co",
#             headers={
#                 "Authorization": f"Bearer {api_key}",
#                 "Content-Type": "application/json"
#             },
#             data=json.dumps(payload),
#             timeout=120
#         )

#         if cr.status_code != 200:
#             raise Exception(f"Crystal API error: {cr.text}")

#         resp = cr.json()

#         if "url" not in resp:
#             raise Exception(f"Crystal response missing URL: {resp}")

#         result_url = resp["url"]

#         # ------------------------------------------------------------------
#         # STEP 3 — Download the final image from Crystal
#         # ------------------------------------------------------------------
#         out_bytes = requests.get(result_url, timeout=120).content
#         out_img = Image.open(BytesIO(out_bytes)).convert("RGB")

#         out_np = np.array(out_img).astype(np.float32) / 255.0
#         out_np = np.expand_dims(out_np, 0)

#         return (out_np,)


# NODE_CLASS_MAPPINGS = {
#     "CrystalUpscaler": CrystalUpscaler
# }

# NODE_DISPLAY_NAME_MAPPINGS = {
#     "CrystalUpscaler": "Crystal AI Upscaler"
# }

import os
import json
import requests
import numpy as np
from PIL import Image
from io import BytesIO


class CrystalUpscaler:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_factor": ("INT", {"default": 2, "min": 1, "max": 200}),
                "creativity": ("INT", {"default": 0, "min": 0, "max": 10}),
            },
            "optional": {
                "api_key_override": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "go"
    CATEGORY = "CrystalAI"

    def go(self, image, scale_factor, creativity, api_key_override):

        # 1) Resolve API key
        api_key = api_key_override.strip() or os.getenv("CRYSTAL_API_KEY", "")
        if not api_key:
            raise Exception("Missing API key: supply override or set CRYSTAL_API_KEY env var.")

        # 2) Convert ComfyUI tensor -> PNG bytes
        pil = Image.fromarray((image[0].cpu().numpy() * 255).astype(np.uint8))
        buf = BytesIO()
        pil.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        # 3) Upload to your private host (/put_crystal)
        upload_url = "https://ace.genfrontai.com:3000/put_crystal"
        r = requests.post(
            upload_url,
            files={"file": ("input.png", img_bytes, "image/png")},
            timeout=60,
        )

        if r.status_code != 200:
            raise Exception(f"Upload failed: {r.status_code} {r.text}")

        data = r.json()
        if "url" not in data:
            raise Exception(f"Upload response missing url: {data}")

        image_url = data["url"]

        # 4) Call Crystal API with that URL
        payload = {
            "mode": "crystal",
            "image": image_url,
            "scale_factor": scale_factor,
            "creativity": creativity,
            "output_format": "png",
        }

        cr = requests.post(
            "https://api-upscale.clarityai.co",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=120,
        )

        if cr.status_code != 200:
            raise Exception(f"Crystal HTTP error: {cr.status_code} {cr.text}")

        resp = cr.json()

        # Crystal: { "status": 200, "message": "<image_url>", ... }
        if resp.get("status") != 200 or "message" not in resp:
            raise Exception(f"Unexpected Crystal response: {resp}")

        result_url = resp["message"]

        # 5) Download final image from Crystal
        out_bytes = requests.get(result_url, timeout=120).content
        out_img = Image.open(BytesIO(out_bytes)).convert("RGB")

        out_np = np.array(out_img).astype(np.float32) / 255.0
        out_np = np.expand_dims(out_np, 0)

        return (out_np,)


NODE_CLASS_MAPPINGS = {
    "CrystalUpscaler": CrystalUpscaler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CrystalUpscaler": "Crystal AI Upscaler",
}
