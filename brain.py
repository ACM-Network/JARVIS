"""
brain.py — AI Brain for JARVIS
Two-layer intelligence:
  1. Ollama (local LLM) — if installed and model is available
  2. Rule-based NLP — fast, zero-dependency fallback

Ollama is completely free, runs offline, and requires no API key.
Install: https://ollama.com  then run: ollama pull phi3:mini
"""

import re
import random
from utils import logger

# ── Try to import Ollama client ───────────────────────────────────────────────
try:
    import ollama as _ollama_lib
    _ollama_available = True
except ImportError:
    _ollama_available = False
    logger.warning("ollama Python package not installed. Using rule-based brain.")
    logger.warning("Install: pip install ollama  (and: ollama pull phi3:mini)")


class Brain:
    """
    Processes natural language queries and returns intelligent responses.
    Uses Ollama (local LLM) when available, falls back to rule-based system.
    """

    JARVIS_SYSTEM_PROMPT = """You are JARVIS, a sophisticated AI assistant inspired by 
the AI from the Marvel films. You are helpful, precise, and slightly witty. 
You address the user as "Sir" or "Ma'am" and maintain a calm, intelligent tone. 
Keep responses concise (2-4 sentences max) since they will be spoken aloud.
Do not use markdown formatting, bullet points, or special characters.
Speak naturally as if having a conversation."""

    # Model preference order — smallest/fastest first
    PREFERRED_MODELS = ["phi3:mini", "phi3", "llama3.2:1b", "gemma:2b", "mistral"]

    def __init__(self):
        self._llm_model = None
        self._use_llm = False
        self._rule_engine = RuleBasedBrain()

        if _ollama_available:
            self._init_ollama()

    # ── Ollama (local LLM) ────────────────────────────────────────────────────

    def _init_ollama(self):
        """Try to connect to Ollama and find an available model."""
        try:
            available = _ollama_lib.list()
            model_names = [m["model"] if isinstance(m, dict) else m.model
                           for m in available.get("models", [])]

            if not model_names:
                logger.warning(
                    "Ollama is running but no models are installed.\n"
                    "Run: ollama pull phi3:mini"
                )
                return

            # Pick the best available model from our preference list
            for preferred in self.PREFERRED_MODELS:
                for available_name in model_names:
                    if preferred in available_name.lower():
                        self._llm_model = available_name
                        self._use_llm = True
                        logger.info(f"Ollama model selected: {self._llm_model}")
                        return

            # If none of our preferred models found, use whatever is available
            self._llm_model = model_names[0]
            self._use_llm = True
            logger.info(f"Ollama model selected (fallback): {self._llm_model}")

        except Exception as e:
            logger.warning(f"Ollama not reachable ({e}). Using rule-based brain.")

    def _ask_ollama(self, user_input: str) -> str:
        """Send a query to Ollama and return the response."""
        try:
            response = _ollama_lib.chat(
                model=self._llm_model,
                messages=[
                    {"role": "system", "content": self.JARVIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                options={
                    "num_predict": 150,    # max tokens to generate (~100 words)
                    "temperature": 0.7,    # creativity level
                    "top_p": 0.9,
                },
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return None

    # ── Public interface ──────────────────────────────────────────────────────

    def think(self, user_input: str) -> str:
        """
        Main entry point. Returns a response string.
        Tries LLM first, falls back to rule-based system.
        """
        if self._use_llm:
            logger.info(f"Querying Ollama ({self._llm_model})...")
            result = self._ask_ollama(user_input)
            if result:
                return result
            logger.warning("LLM returned nothing — falling back to rules.")

        return self._rule_engine.respond(user_input)


# ── Rule-Based Fallback Brain ─────────────────────────────────────────────────

class RuleBasedBrain:
    """
    Fast, lightweight NLP using keyword matching and templates.
    Covers the most common conversational intents.
    No ML required — pure Python.
    """

    GREETINGS = [
        "Good day, Sir. How may I assist you?",
        "At your service. What do you require?",
        "Online and ready, Sir. What can I do for you?",
    ]

    THANKS_RESPONSES = [
        "You are most welcome, Sir.",
        "Always a pleasure to be of assistance.",
        "My pleasure entirely, Sir.",
    ]

    IDENTITY_RESPONSES = [
        ("I am JARVIS — Just A Rather Very Intelligent System. "
         "Your personal AI assistant, Sir."),
        ("JARVIS at your service. I was designed to assist you with "
         "information, system control, and general queries."),
    ]

    UNKNOWN_RESPONSES = [
        "I'm afraid I don't have a specific answer for that, Sir. "
        "You may want to refine your query.",
        "That query is outside my current knowledge base. "
        "Perhaps I can help with something else?",
        "Interesting question, Sir. Unfortunately, my rule-based systems "
        "don't cover that. Try installing Ollama for full AI responses.",
    ]

    # intent_name: (patterns, responses)
    INTENTS: dict = {
        "greeting": (
            [r"\b(hello|hi|hey|good morning|good evening|good afternoon)\b"],
            GREETINGS,
        ),
        "thanks": (
            [r"\b(thank you|thanks|cheers|appreciate)\b"],
            THANKS_RESPONSES,
        ),
        "identity": (
            [r"\b(who are you|what are you|your name|introduce yourself)\b"],
            IDENTITY_RESPONSES,
        ),
        "capabilities": (
            [r"\b(what can you do|your capabilities|help me|how can you help)\b"],
            [
                "I can tell you the time and date, open applications, "
                "search the web, check the weather, control system volume, "
                "answer general questions, and much more, Sir.",
            ],
        ),
        "joke": (
            [r"\b(tell me a joke|make me laugh|something funny|joke)\b"],
            [
                "Why do programmers prefer dark mode? Because light attracts bugs, Sir.",
                "I tried to write a joke about infinity, but I kept going on and on.",
                "There are 10 types of people in the world: those who understand "
                "binary, and those who don't, Sir.",
            ],
        ),
        "feeling": (
            [r"\b(how are you|are you okay|you alright|you doing)\b"],
            [
                "All systems nominal, Sir. Running at peak efficiency.",
                "Fully operational and ready to assist. Thank you for asking.",
            ],
        ),
        "weather_general": (
            [r"\b(weather|temperature|hot|cold|rain|sunny|forecast)\b"],
            [
                "For specific weather information, say 'weather in [city]' "
                "and I will look that up for you, Sir.",
            ],
        ),
        "meaning_of_life": (
            [r"\b(meaning of life|purpose of life|42)\b"],
            [
                "That would be 42, Sir. Though the question may be more "
                "important than the answer.",
            ],
        ),
    }

    def respond(self, user_input: str) -> str:
        text = user_input.lower().strip()

        for intent, (patterns, responses) in self.INTENTS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    logger.debug(f"Rule-based intent matched: {intent}")
                    return random.choice(responses)

        return random.choice(self.UNKNOWN_RESPONSES)
