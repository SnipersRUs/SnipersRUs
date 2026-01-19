#!/usr/bin/env python3
"""
On-Chain Data Fetcher
Fetches blockchain data from free APIs (Etherscan, Solana RPC, Blockstream)
"""
import requests
import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class EtherscanClient:
    """Client for Etherscan API (Ethereum blockchain data)"""

    def __init__(self, api_key: str):
        """
        Initialize Etherscan client

        Args:
            api_key: Etherscan API key (free tier available)
        """
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"

    def get_latest_block(self) -> Optional[int]:
        """Get the latest Ethereum block number"""
        try:
            params = {
                "module": "proxy",
                "action": "eth_blockNumber",
                "apikey": self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1':
                block_hex = data.get('result', '0x0')
                return int(block_hex, 16)
            return None
        except Exception as e:
            logger.error(f"Error fetching latest block: {e}")
            return None

    def get_block_info(self, block_number: int) -> Optional[Dict]:
        """Get information about a specific block"""
        try:
            params = {
                "module": "proxy",
                "action": "eth_getBlockByNumber",
                "tag": hex(block_number),
                "boolean": "true",
                "apikey": self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get('result')
        except Exception as e:
            logger.error(f"Error fetching block info: {e}")
            return None

    def get_balance(self, address: str) -> Optional[float]:
        """Get ETH balance for an address (in ETH)"""
        try:
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
                "apikey": self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == '1':
                balance_wei = int(data.get('result', '0'))
                balance_eth = balance_wei / 1e18
                return balance_eth
            return None
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction details by hash"""
        try:
            params = {
                "module": "proxy",
                "action": "eth_getTransactionByHash",
                "txhash": tx_hash,
                "apikey": self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get('result')
        except Exception as e:
            logger.error(f"Error fetching transaction: {e}")
            return None


class SolanaClient:
    """Client for Solana RPC (public endpoints)"""

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        """
        Initialize Solana client

        Args:
            rpc_url: Solana RPC endpoint (default: public mainnet)
        """
        self.rpc_url = rpc_url

    def _rpc_call(self, method: str, params: list) -> Optional[Dict]:
        """Make an RPC call to Solana"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get('result')
        except Exception as e:
            logger.error(f"Error in Solana RPC call: {e}")
            return None

    def get_slot(self) -> Optional[int]:
        """Get the current slot number"""
        return self._rpc_call("getSlot", [])

    def get_block_height(self) -> Optional[int]:
        """Get the current block height"""
        return self._rpc_call("getBlockHeight", [])

    def get_account_info(self, address: str) -> Optional[Dict]:
        """Get account information"""
        return self._rpc_call("getAccountInfo", [address, {"encoding": "jsonParsed"}])

    def get_balance(self, address: str) -> Optional[float]:
        """Get SOL balance for an address (in SOL)"""
        result = self._rpc_call("getBalance", [address])
        if result:
            lamports = result.get('value', 0)
            return lamports / 1e9  # Convert lamports to SOL
        return None


class BitcoinClient:
    """Client for Blockstream API (Bitcoin blockchain data)"""

    def __init__(self, network: str = "mainnet"):
        """
        Initialize Bitcoin client

        Args:
            network: Network to use ('mainnet' or 'testnet')
        """
        if network == "mainnet":
            self.base_url = "https://blockstream.info/api"
        else:
            self.base_url = "https://blockstream.info/testnet/api"

    def get_latest_block_height(self) -> Optional[int]:
        """Get the latest block height"""
        try:
            response = requests.get(f"{self.base_url}/blocks/tip/height", timeout=10)
            response.raise_for_status()
            return int(response.text)
        except Exception as e:
            logger.error(f"Error fetching latest block height: {e}")
            return None

    def get_block_info(self, block_height: int) -> Optional[Dict]:
        """Get information about a specific block"""
        try:
            response = requests.get(f"{self.base_url}/block-height/{block_height}", timeout=10)
            response.raise_for_status()
            block_hash = response.text.strip()

            # Get block details
            response = requests.get(f"{self.base_url}/block/{block_hash}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching block info: {e}")
            return None

    def get_address_info(self, address: str) -> Optional[Dict]:
        """Get address information"""
        try:
            response = requests.get(f"{self.base_url}/address/{address}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching address info: {e}")
            return None

    def get_transaction(self, tx_id: str) -> Optional[Dict]:
        """Get transaction details"""
        try:
            response = requests.get(f"{self.base_url}/tx/{tx_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching transaction: {e}")
            return None



