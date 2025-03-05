"""
Contract initialization module for the Goldilocks DeFi bot.
Handles loading ABIs and initializing contract instances.
"""
import json
import config
from web3_utils import w3


def load_abi(filename):
    """
    Load ABI from JSON file.
    
    Args:
        filename: Path to ABI JSON file
        
    Returns:
        ABI as a Python object
    """
    with open(filename) as f:
        return json.load(f)


# Load contract ABIs
try:
    honey_abi = load_abi(config.HONEY_ABI_PATH)
    locks_abi = load_abi(config.LOCKS_ABI_PATH)
    porridge_abi = load_abi(config.PORRIDGE_ABI_PATH)
except FileNotFoundError as e:
    raise FileNotFoundError(f"ABI file not found: {e}. Make sure the ABI files exist in the {config.ABI_DIR} directory.")
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON in ABI file: {e}")

# Initialize contract instances
honey_contract = w3.eth.contract(address=config.HONEY_ADDRESS, abi=honey_abi)
locks_contract = w3.eth.contract(address=config.LOCKS_ADDRESS, abi=locks_abi)
porridge_contract = w3.eth.contract(address=config.PORRIDGE_ADDRESS, abi=porridge_abi)

# Verify contract connections by calling view functions
try:
    honey_symbol = honey_contract.functions.symbol().call()
    locks_symbol = locks_contract.functions.symbol().call()
    porridge_symbol = porridge_contract.functions.symbol().call()
    
    print(f"Connected to contracts: {honey_symbol}, {locks_symbol}, and {porridge_symbol}")
except Exception as e:
    raise Exception(f"Failed to connect to one or more contracts: {e}")
