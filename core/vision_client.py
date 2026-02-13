from core.llm import model_router
from smolagents import OpenAIServerModel
import base64
import structlog
import json

logger = structlog.get_logger()

class VisionClient:
    """
    Dedicated client for Vision tasks (The Eyes).
    Uses model_router.vision (gpt-5.2-pro).
    """
    def __init__(self):
        if not model_router:
            raise RuntimeError("ModelRouter unavailable.")
        self.model = model_router.vision

    def encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def get_coordinates(self, image_path: str, query: str) -> tuple[int, int]:
        """
        Ask the Vision Model to find the (x, y) coordinates of a UI element.
        Returns: (x, y) or raises Exception.
        """
        logger.info("vision_query_start", query=query)
        
        # Construct the prompt specifically for coordinate extraction
        prompt = f"""
        Analyze this screenshot. Find the center coordinates (x, y) of the UI element described as: '{query}'.
        Return ONLY the coordinates in the format: x, y
        If the element is not found, return: NOT_FOUND
        """
        
        # Note: smolagents doesn't support 'image' input in .generate() natively in the same way raw OpenAI does sometimes.
        # However, OpenAIServerModel in smolagents might support multimodal messages if we format them correctly.
        # Since we are "God Mode", we might need to use the raw client inside the model or handle it carefully.
        # For V2 Phase 2, we will attempt to construct a multimodal message if the underlying library supports it,
        # otherwise we might need a custom raw call. 
        
        # Let's try the standard OpenAI format which smolagents *should* pass through if using chat completion.
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.encode_image(image_path)}"
                        }
                    }
                ]
            }
        ]
        
        try:
            # We bypass smolagents generate() to ensure we pass the image properly if generate() expects strict types.
            # model_router.vision is an OpenAIServerModel instance.
            # It has a self.client (OpenAI client).
            
            response = self.model.client.chat.completions.create(
                model=self.model.model_id,
                messages=messages,
                max_completion_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            logger.info("vision_query_result", content=content)
            
            if "NOT_FOUND" in content:
                raise ValueError(f"Vision model could not find '{query}'")
            
            # Parse "123, 456"
            parts = content.split(",")
            x = int(parts[0].strip())
            y = int(parts[1].strip())
            
            return x, y
            
        except Exception as e:
            logger.error("vision_query_failed", error=str(e))
            raise e

    def find_text(self, image_path: str, query: str, region_hint: str = "top section") -> dict:
        """
        Ask the Vision Model to find text matching query and return coords.
        Returns dict: {found: bool, text: str, x: int, y: int}
        """
        logger.info("vision_text_query_start", query=query, region=region_hint)

        prompt = f"""
        Analyze this screenshot and locate the best match for the text query: '{query}'.
        Focus on the region: '{region_hint}'.
        Return JSON only:
        {{\"found\": true, \"text\": \"...\", \"x\": 123, \"y\": 456}}
        If not found, return:
        {{\"found\": false}}
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.encode_image(image_path)}"
                        }
                    }
                ]
            }
        ]

        try:
            response = self.model.client.chat.completions.create(
                model=self.model.model_id,
                messages=messages,
                max_completion_tokens=800,
            )
            content = response.choices[0].message.content.strip()
            logger.info("vision_text_query_result", content=content)
            data = json.loads(content)
            if not isinstance(data, dict):
                return {"found": False}
            return data
        except Exception as e:
            logger.error("vision_text_query_failed", error=str(e))
            raise e

# Singleton
vision_client = VisionClient()
