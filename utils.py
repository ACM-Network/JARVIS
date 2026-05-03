"""
utils.py — Shared utilities for JARVIS
  - logger: consistent logging across all modules
  - display_banner(): startup ASCII art
"""

import logging
import sys

# ── Logger ────────────────────────────────────────────────────────────────────

def _create_logger() -> logging.Logger:
    log = logging.getLogger("JARVIS")
    log.setLevel(logging.INFO)

    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        log.addHandler(handler)

    return log

logger = _create_logger()

# ── ASCII Banner ──────────────────────────────────────────────────────────────

BANNER = r"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝

  Just A Rather Very Intelligent System v1.0
  ─────────────────────────────────────────
  Offline · Free · Open Source
  Say "Jarvis" to activate
"""

def display_banner():
    print(BANNER)
