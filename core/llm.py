from smolagents import OpenAIServerModel
import os
from dotenv import load_dotenv
from core.responses_model import ResponsesModel

load_dotenv()

class ModelRouter:
    """
    Routes tasks to the appropriate GPT-5.2 model variant.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env")

        # Model IDs (override via env if needed)
        # Accuracy-first defaults (Responses API for non-chat models)
        self.planner_id = os.getenv("ARKA_PLANNER_MODEL", "gpt-5.2-pro-2025-12-11")
        self.executor_id = os.getenv("ARKA_EXECUTOR_MODEL", "gpt-5.2-chat-latest")
        self.vision_id = os.getenv("ARKA_VISION_MODEL", "gpt-4o-2024-11-20")
        self.router_id = os.getenv("ARKA_ROUTER_MODEL", "gpt-5.1-2025-11-13")
        self.verifier_id = os.getenv("ARKA_VERIFIER_MODEL", "gpt-5.2-pro-2025-12-11")

        # Planner: High Reasoning, large context, hallucination resistance
        self._planner_fallback = OpenAIServerModel(
            model_id="gpt-5.2-chat-latest",
            api_key=self.api_key,
        )
        self.planner = ResponsesModel(
            model_id=self.planner_id,
            api_key=self.api_key,
            fallback=self._planner_fallback,
        )
        
        # Executor: Specific fine-tuning for Agentic Coding & Tool Use
        self.executor = OpenAIServerModel(
            model_id=self.executor_id,
            api_key=self.api_key,
        )
        
        # Vision: High fidelity vision capabilities (re-using Pro for now)
        self.vision = OpenAIServerModel(
            model_id=self.vision_id,
            api_key=self.api_key,
        )

        # Router: Fast intent classification & task resolution
        self._router_fallback = OpenAIServerModel(
            model_id="gpt-5.1-chat-latest",
            api_key=self.api_key,
        )
        self.router = ResponsesModel(
            model_id=self.router_id,
            api_key=self.api_key,
            fallback=self._router_fallback,
        )

        # Verifier: Strict post-hoc verification
        self._verifier_fallback = OpenAIServerModel(
            model_id="gpt-5.2-chat-latest",
            api_key=self.api_key,
        )
        self.verifier = ResponsesModel(
            model_id=self.verifier_id,
            api_key=self.api_key,
            fallback=self._verifier_fallback,
        )
        
        # --- OBSERVABILITY INJECTION ---
        try:
            from langfuse.openai import OpenAI as LangfuseOpenAI
            # Replace the internal vanilla OpenAI clients with Langfuse-instrumented ones
            instrumented_client = LangfuseOpenAI(api_key=self.api_key)

            # Chat-completions models
            self._planner_fallback.client = instrumented_client
            self._router_fallback.client = instrumented_client
            self._verifier_fallback.client = instrumented_client
            self.executor.client = instrumented_client
            self.vision.client = instrumented_client

            # Responses API models
            self.planner.client = instrumented_client
            self.router.client = instrumented_client
            self.verifier.client = instrumented_client
            print("✅ Langfuse Observability injected into Models.")
        except Exception as e:
            print(f"⚠️ Failed to inject Langfuse Observability: {e}")

# Global singleton
try:
    model_router = ModelRouter()
except Exception as e:
    print(f"Warning: ModelRouter failed to initialize (Env variables missing?): {e}")
    model_router = None
