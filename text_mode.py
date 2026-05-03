"""
text_mode.py — Test JARVIS without microphone or speakers.
Type commands in the terminal. Great for development and testing.

Run: python text_mode.py
"""

from brain import Brain
from commands import CommandProcessor
from utils import display_banner, logger


def main():
    display_banner()
    brain = Brain()
    commands = CommandProcessor()

    print("=" * 55)
    print("  JARVIS Text Mode — Type commands, press Enter")
    print("  Type 'quit' or 'exit' to stop")
    print("=" * 55 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[JARVIS]: Goodbye, Sir.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "goodbye", "shut down"):
            print("[JARVIS]: Goodbye, Sir. It has been a pleasure.")
            break

        # Try built-in command first
        result = commands.process(user_input)
        if result:
            print(f"[JARVIS]: {result}\n")
            continue

        # Fall back to AI brain
        result = brain.think(user_input)
        print(f"[JARVIS]: {result}\n")


if __name__ == "__main__":
    main()
