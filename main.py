"""
JARVIS - Just A Rather Very Intelligent System
Main entry point. Starts the assistant and keeps it running.
"""

import sys
import time
from voice import VoiceEngine
from brain import Brain
from commands import CommandProcessor
from utils import logger, display_banner

def main():
    display_banner()
    logger.info("Initializing JARVIS...")

    # Initialize all modules
    brain = Brain()
    commands = CommandProcessor()
    voice = VoiceEngine(wake_word="jarvis")

    logger.info("All systems online. Awaiting wake word...")
    voice.speak("All systems online. Good day, Sir. Say 'Jarvis' to activate me.")

    while True:
        try:
            # Step 1: Listen for wake word
            logger.info("Listening for wake word...")
            if not voice.wait_for_wake_word():
                continue  # No wake word heard, keep listening

            # Step 2: Wake word detected — give audio cue
            voice.speak("Yes, Sir?")
            logger.info("Wake word detected. Listening for command...")

            # Step 3: Listen for the actual command
            user_input = voice.listen_for_command()
            if not user_input:
                voice.speak("I did not catch that, Sir. Please try again.")
                continue

            logger.info(f"Command received: {user_input}")

            # Step 4: Check for exit commands
            if any(word in user_input.lower() for word in ["goodbye", "shut down", "exit", "quit", "sleep"]):
                voice.speak("Goodbye, Sir. It has been a pleasure assisting you.")
                break

            # Step 5: Try built-in commands first (fast, no AI needed)
            command_result = commands.process(user_input)
            if command_result:
                voice.speak(command_result)
                continue

            # Step 6: Fall back to AI brain for complex queries
            logger.info("Routing to AI brain...")
            ai_response = brain.think(user_input)
            voice.speak(ai_response)

        except KeyboardInterrupt:
            voice.speak("Shutting down. Goodbye, Sir.")
            logger.info("JARVIS terminated by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            voice.speak("I encountered an unexpected error, Sir. Standing by.")
            time.sleep(1)

if __name__ == "__main__":
    main()
