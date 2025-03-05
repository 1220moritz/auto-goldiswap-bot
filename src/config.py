"""
Configuration module for the Goldilocks DeFi bot.
Handles loading and validating environment variables.
"""
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# Required environment variables
RPC_URL = os.getenv("RPC_URL")
if not RPC_URL:
    raise ValueError("RPC_URL not set in .env")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY not set in .env")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL not set in .env")

# Contract addresses
HONEY_ADDRESS = os.getenv("HONEY_ADDRESS")
if not HONEY_ADDRESS:
    raise ValueError("HONEY_ADDRESS not set in .env")
HONEY_ADDRESS = Web3.to_checksum_address(HONEY_ADDRESS)

LOCKS_ADDRESS = os.getenv("LOCKS_ADDRESS")
if not LOCKS_ADDRESS:
    raise ValueError("LOCKS_ADDRESS not set in .env")
LOCKS_ADDRESS = Web3.to_checksum_address(LOCKS_ADDRESS)

PORRIDGE_ADDRESS = os.getenv("PORRIDGE_ADDRESS")
if not PORRIDGE_ADDRESS:
    raise ValueError("PORRIDGE_ADDRESS not set in .env")
PORRIDGE_ADDRESS = Web3.to_checksum_address(PORRIDGE_ADDRESS)

# Optional configuration with defaults
BORROW_THRESHOLD = int(os.getenv("BORROW_THRESHOLD", "1000000000000000000"))  # Default: 1 token (18 decimals)
ALLOW_WALLET_HONEY = os.getenv("ALLOW_WALLET_HONEY", "false").lower() == "true"
SWAP_LEFTOVER_HONEY = os.getenv("SWAP_LEFTOVER_HONEY", "false").lower() == "true"
CYCLE_INTERVAL = int(os.getenv("CYCLE_INTERVAL", "120"))  # Default: 2 minutes
SWAP_ALL_WALLET_HONEY = os.getenv("SWAP_ALL_WALLET_HONEY", "false").lower() == "true"

# Token precision (for display purposes)
TOKEN_DECIMALS = 18
TOKEN_PRECISION = 10 ** TOKEN_DECIMALS

# Define paths for ABI files
ABI_DIR = "ABIs"
HONEY_ABI_PATH = f"{ABI_DIR}/abi_honey.json"
LOCKS_ABI_PATH = f"{ABI_DIR}/abi_locks.json"
PORRIDGE_ABI_PATH = f"{ABI_DIR}/abi_porridge.json"
