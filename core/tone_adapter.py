"""
core/tone_adapter.py — Adaptive Communication (Phase 6.5)

Analyzes user messages for emotional/urgency signals and generates
a tone directive that is injected into the system prompt.

Signals detected:
  - Message length → short = urgent, long = detailed
  - Punctuation → "!!!" = excited, "?" = curious, "..." = uncertain
  - Keywords → "ASAP", "urgent", "please", "help", "thanks"
  - Caps → all caps = frustrated/urgent
"""

import re
import structlog

logger = structlog.get_logger()


class ToneAdapter:
    """Detects user tone and generates adaptive response directives."""

    def detect_tone(self, message: str) -> str:
        """
        Analyze a user message and return a tone directive string
        to inject into the system prompt.
        """
        if not message:
            return ""

        signals = {
            "length": len(message),
            "has_exclamation": "!" in message,
            "has_question": "?" in message,
            "has_ellipsis": "..." in message,
            "all_caps_ratio": sum(1 for c in message if c.isupper()) / max(len(message), 1),
            "has_urgency": any(w in message.lower() for w in ["asap", "urgent", "now", "quickly", "fast", "hurry"]),
            "has_politeness": any(w in message.lower() for w in ["please", "thanks", "thank you", "could you", "would you"]),
            "has_frustration": any(w in message.lower() for w in ["why isn't", "doesn't work", "broken", "failed", "error", "wrong"]),
            "has_greeting": any(w in message.lower() for w in ["hey", "hi", "hello", "good morning", "what's up"]),
        }

        # Decision tree for tone
        if signals["has_urgency"] or (signals["length"] < 15 and signals["all_caps_ratio"] > 0.5):
            tone = "URGENT"
            directive = "User is in a rush. Be EXTREMELY concise — one-line answers preferred. Skip explanations. Act immediately."
        elif signals["has_frustration"]:
            tone = "FRUSTRATED"
            directive = "User seems frustrated. Acknowledge the issue briefly, then provide a clear fix. Avoid filler words."
        elif signals["has_greeting"]:
            tone = "CASUAL"
            directive = "User is being casual. Be warm and friendly. It's okay to be slightly conversational."
        elif signals["has_politeness"] and signals["length"] > 50:
            tone = "DETAILED"
            directive = "User is asking thoughtfully. Provide a thorough, well-structured response. Include reasoning."
        elif signals["has_question"] and signals["length"] < 30:
            tone = "QUICK_QUESTION"
            directive = "User has a quick question. Give a direct, precise answer."
        elif signals["length"] < 10:
            tone = "TERSE"
            directive = "User is being very brief. Match their energy — respond concisely."
        else:
            tone = "PROFESSIONAL"
            directive = "User message is neutral. Respond in a professional, balanced tone."

        logger.debug("tone_detected", tone=tone, length=signals["length"])
        return f"\n## 🎭 TONE DIRECTIVE\n{directive}\n"


# Singleton
tone_adapter = ToneAdapter()
