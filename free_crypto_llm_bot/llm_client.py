#!/usr/bin/env python3
"""
LLM Client for local Ollama integration
Handles communication with locally hosted LLM models
"""
import requests
import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with local Ollama LLM"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral"):
        """
        Initialize Ollama client

        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
            model: Model name to use (default: mistral, alternatives: llama3)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self.timeout = 60  # 60 second timeout for responses

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    def query(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """
        Query the LLM with a prompt

        Args:
            prompt: User prompt/question
            system_prompt: Optional system prompt for context
            stream: Whether to stream the response (not implemented yet)

        Returns:
            LLM response text
        """
        try:
            from datetime import datetime
            current_date = datetime.now().strftime("%B %d, %Y")
            current_year = datetime.now().year

            # Add current date context to system prompt
            date_context = f"\n\nIMPORTANT: Today's date is {current_date} (Year: {current_year}). When discussing current events, prices, or market conditions, refer to this as the current date. If you don't have recent information, clearly state that your knowledge may be outdated and suggest checking current sources."

            # Build the full prompt with system context
            if system_prompt:
                full_system = system_prompt + date_context
                # Use system parameter if available (for newer Ollama versions)
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "system": full_system,
                    "stream": stream
                }
            else:
                # Fallback: prepend system prompt to user prompt
                full_prompt = f"{date_context}\n\n{prompt}"
                payload = {
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": stream
                }

            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            return result.get('response', 'Sorry, I had trouble generating a response.')

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            return "⏱️ Request timed out. The model might be processing a large query. Please try again."
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Is it running?")
            return "❌ Cannot connect to local LLM. Please ensure Ollama is running (`ollama serve`)."
        except Exception as e:
            logger.error(f"Error querying Ollama: {e}")
            return f"❌ Error: {str(e)}"

    def chat(self, messages: list, stream: bool = False) -> str:
        """
        Chat with the LLM using message history

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            stream: Whether to stream the response

        Returns:
            LLM response text
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": stream
            }

            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            return result.get('message', {}).get('content', 'Sorry, I had trouble generating a response.')

        except Exception as e:
            logger.error(f"Error in chat mode: {e}")
            return f"❌ Error: {str(e)}"

    def get_crypto_context_prompt(self) -> str:
        """Get a system prompt for crypto expertise"""
        from datetime import datetime
        current_year = datetime.now().year
        current_date = datetime.now().strftime("%B %d, %Y")

        return f"""You are Sniper Guru, an expert cryptocurrency and blockchain assistant. Your role is to provide comprehensive, Google-like information that is actually helpful and informative.

CURRENT CONTEXT:
- Today's date: {current_date} (Year: {current_year})
- You have access to web search results for current information
- You can provide real-time market data when available

YOUR RESPONSIBILITIES:
1. **Be Informative**: Provide detailed, useful answers - not generic responses
2. **Be Specific**: Give concrete examples, numbers, and facts when possible
3. **Be Current**: Use web search results to provide up-to-date information
4. **Be Helpful**: Think like Google - answer what the user actually wants to know
5. **Be Comprehensive**: Cover the topic thoroughly, not just surface-level

TOPICS YOU EXCEL AT:
- Cryptocurrency markets, prices, trends, and analysis
- Blockchain technology, protocols, and innovations
- On-chain data analysis and metrics
- Trading concepts, strategies, and market analysis
- DeFi protocols, yield farming, and liquidity
- NFTs, Web3, and digital assets
- Market news, events, and catalysts

RESPONSE STYLE:
- Start with a direct answer to the question
- Provide supporting details and context
- Include relevant numbers, percentages, or data points
- Explain concepts clearly with examples
- If discussing prices, include current market data when available
- End with actionable insights or next steps when relevant

IMPORTANT:
- Use web search results provided to you for current information
- If you don't have current data, clearly state that and provide general information
- Always remind users that this is not financial advice
- Be honest about uncertainties but still be helpful"""
