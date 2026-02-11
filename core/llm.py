from smolagents import OpenAIServerModel
import os
from dotenv import load_dotenv

load_dotenv()

class ModelRouter:
    """
    Routes tasks to the appropriate GPT-5.2 model variant.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env")

        # Planner: High Reasoning, large context, hallucination resistance
        self.planner_id = "gpt-5.2-chat-latest" 
        self.planner = OpenAIServerModel(
            model_id=self.planner_id,
            api_key=self.api_key,
        )
        
        # Executor: Specific fine-tuning for Agentic Coding & Tool Use
        self.executor_id = "gpt-5.2-chat-latest"
        self.executor = OpenAIServerModel(
            model_id=self.executor_id,
            api_key=self.api_key,
        )
        
        # Vision: High fidelity vision capabilities (re-using Pro for now)
        self.vision_id = "gpt-5.2-chat-latest"
        self.vision = OpenAIServerModel(
            model_id=self.vision_id,
            api_key=self.api_key,
        )
        
        # --- OBSERVABILITY INJECTION ---
        try:
            from langfuse.openai import OpenAI as LangfuseOpenAI
            # Replace the internal vanilla OpenAI clients with Langfuse-instrumented ones
            instrumented_client = LangfuseOpenAI(api_key=self.api_key)
            
            self.planner.client = instrumented_client
            self.executor.client = instrumented_client
            self.vision.client = instrumented_client
            print("✅ Langfuse Observability injected into Models.")
        except Exception as e:
            print(f"⚠️ Failed to inject Langfuse Observability: {e}")

# Global singleton
try:
    model_router = ModelRouter()
except Exception as e:
    print(f"Warning: ModelRouter failed to initialize (Env variables missing?): {e}")
    model_router = None
