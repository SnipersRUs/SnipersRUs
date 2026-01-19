#!/usr/bin/env python3
"""
Run script for bot with slash commands (no Message Content Intent needed)
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from free_crypto_llm_bot.bot_slash_commands import main

if __name__ == "__main__":
    main()



