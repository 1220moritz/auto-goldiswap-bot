import pytest
import json
import os
from decimal import Decimal
from web3 import Web3

# Import environment variables for testing
from dotenv import load_dotenv

load_dotenv()

# Environment variables
RPC_URL = os.getenv("RPC_URL")
HONEY_ADDRESS = os.getenv("HONEY_ADDRESS")
PORRIDGE_ADDRESS = os.getenv("PORRIDGE_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Skip tests if environment is not set up
if not (RPC_URL and HONEY_ADDRESS and PRIVATE_KEY):
    pytest.skip("Missing RPC_URL, HONEY_ADDRESS, or PRIVATE_KEY in environment", allow_module_level=True)


@pytest.fixture(scope="module")
def web3():
    """Create a Web3 connection to use for all tests"""
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        pytest.skip("Could not connect to Ethereum node", allow_module_level=True)
    return w3


@pytest.fixture(scope="module")
def account(web3):
    """Create account from private key"""
    account = web3.eth.account.from_key(PRIVATE_KEY)
    print(f"\nUsing account: {account.address}")
    return account


@pytest.fixture(scope="module")
def honey_contract(web3):
    """Initialize HONEY contract instance for testing"""
    # Load ABI from file
    abi_path = "../src/ABIs/abi_honey.json"
    try:
        with open(abi_path, 'r') as f:
            honey_abi = json.load(f)
    except FileNotFoundError:
        pytest.skip(f"HONEY ABI file not found at {abi_path}", allow_module_level=True)

    # Initialize contract
    contract = web3.eth.contract(
        address=web3.to_checksum_address(HONEY_ADDRESS),
        abi=honey_abi
    )
    return contract


class TestHoneyContract:
    """
    Tests for HONEY token contract read functions.
    These tests interact with the actual blockchain.
    """

    def test_contract_connection(self, honey_contract):
        """Test basic connection to the HONEY contract"""
        assert honey_contract.address is not None
        assert Web3.is_checksum_address(honey_contract.address)

    def test_token_info(self, honey_contract):
        """Test basic token information"""
        name = honey_contract.functions.name().call()
        symbol = honey_contract.functions.symbol().call()
        decimals = honey_contract.functions.decimals().call()

        print(f"\nHONEY Token Info: {name} ({symbol}), {decimals} decimals")

        assert isinstance(name, str) and len(name) > 0
        assert isinstance(symbol, str) and len(symbol) > 0
        assert isinstance(decimals, int) and decimals > 0
        # HONEY-specific check
        assert symbol == "HONEY", f"Expected symbol 'HONEY', got '{symbol}'"

    def test_total_supply(self, honey_contract):
        """Test getting the total supply"""
        total_supply = honey_contract.functions.totalSupply().call()

        supply_in_tokens = Decimal(total_supply) / Decimal(10 ** 18)
        print(f"\nHONEY Total Supply: {supply_in_tokens}")

        assert isinstance(total_supply, int)
        assert total_supply > 0

    def test_balance_of(self, honey_contract, account):
        """Test balanceOf function for the bot's account"""
        balance = honey_contract.functions.balanceOf(account.address).call()

        balance_in_tokens = Decimal(balance) / Decimal(10 ** 18)
        print(f"\nHONEY Balance for {account.address}: {balance_in_tokens}")

        assert isinstance(balance, int)
        assert balance >= 0

    def test_allowance_for_porridge(self, honey_contract, account, web3):
        """Test allowance for PORRIDGE contract (important for stir function)"""
        if not PORRIDGE_ADDRESS:
            pytest.skip("No PORRIDGE_ADDRESS provided in environment")

        owner = account.address
        spender = web3.to_checksum_address(PORRIDGE_ADDRESS)

        allowance = honey_contract.functions.allowance(owner, spender).call()

        allowance_in_tokens = Decimal(allowance) / Decimal(10 ** 18)
        print(f"\nHONEY Allowance for PORRIDGE: {allowance_in_tokens}")

        assert isinstance(allowance, int)
        assert allowance >= 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])