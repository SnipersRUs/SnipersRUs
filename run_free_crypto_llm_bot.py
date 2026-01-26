#!/usr/bin/env python3
"""
Run script for Free Crypto LLM Discord Bot
Handles path setup and runs the bot
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the bot
from free_crypto_llm_bot.bot import main

if __name__ == "__main__":
    main()



