#!/usr/bin/env python3
"""
Verify bot setup - check if .env file is configured correctly
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def verify_setup():
    """Verify that the bot is set up correctly"""
    bot_dir = Path(__file__).parent
    env_file = bot_dir / '.env'

    print("🔍 Verifying Free Crypto LLM Bot Setup")
    print("=" * 50)

    # Check if .env exists
    if not env_file.exists():
        print("❌ .env file not found!")
        print(f"   Expected location: {env_file}")
        print("   Run: python setup_env.py to create it")
        return False

    print(f"✅ .env file found: {env_file}")

    # Load environment variables
    load_dotenv(env_file)

    # Check Discord token
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token or discord_token == 'your_discord_bot_token_here':
        print("❌ DISCORD_TOKEN not configured!")
        print("   Please set DISCORD_TOKEN in .env file")
        return False

    print(f"✅ DISCORD_TOKEN configured (length: {len(discord_token)})")

    # Check Ollama config
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'mistral')
    print(f"✅ Ollama URL: {ollama_url}")
    print(f"✅ Ollama Model: {ollama_model}")

    # Check optional APIs
    etherscan = os.getenv('ETHERSCAN_API_KEY')
    coingecko = os.getenv('COINGECKO_API_KEY')

    if etherscan and etherscan != 'your_etherscan_api_key_here':
        print("✅ Etherscan API key configured")
    else:
        print("⚠️  Etherscan API key not configured (optional)")

    if coingecko and coingecko != 'your_coingecko_api_key_here':
        print("✅ CoinGecko API key configured")
    else:
        print("⚠️  CoinGecko API key not configured (optional)")

    print("\n" + "=" * 50)
    print("✅ Setup verification complete!")
    print("\n📋 Next steps:")
    print("   1. Make sure Ollama is running: ollama serve")
    print("   2. Pull a model: ollama pull mistral")
    print("   3. Install dependencies: pip install -r ../requirements.txt")
    print("   4. Run the bot: python ../run_free_crypto_llm_bot.py")
    print("   5. Invite bot to server using the OAuth2 URL")

    return True

if __name__ == "__main__":
    verify_setup()



