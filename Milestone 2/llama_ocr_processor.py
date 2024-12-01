from together import Together
import base64

class LlamaOCRProcessor:
    def __init__(self):
        try:
            self.client = Together()
            self.model = "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"
            self.prompt = """Extract text from the image. Return the text exactly as it appears in the image but with proper formatting. If no text is found, return "No text found."""
        except ImportError:
            print("Together library not found. LlamaOCR will be unavailable.")
            self.client = None
        except Exception as e:
            print(f"Error initializing Together: {e}")
            self.client = None

    def encode_image(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            return None

    def perform_ocr(self, image_path):
        if self.client is None:
            return "Error: Together library not available."

        encoded_image = self.encode_image(image_path)
        if encoded_image is None:
            return "Error: Image not found."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                        ]
                    }
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error performing Llama OCR: {e}"