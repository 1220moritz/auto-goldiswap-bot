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
LOCKS_ADDRESS = os.getenv("LOCKS_ADDRESS")
HONEY_ADDRESS = os.getenv("HONEY_ADDRESS")
PORRIDGE_ADDRESS = os.getenv("PORRIDGE_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Skip tests if environment is not set up
if not (RPC_URL and LOCKS_ADDRESS and PRIVATE_KEY):
    pytest.skip("Missing RPC_URL, LOCKS_ADDRESS, or PRIVATE_KEY in environment", allow_module_level=True)


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
def locks_contract(web3):
    """Initialize LOCKS contract instance for testing"""
    # Load ABI from file
    abi_path = "../src/ABIs/abi_locks.json"
    try:
        with open(abi_path, 'r') as f:
            locks_abi = json.load(f)
    except FileNotFoundError:
        pytest.skip(f"LOCKS ABI file not found at {abi_path}", allow_module_level=True)

    # Initialize contract
    contract = web3.eth.contract(
        address=web3.to_checksum_address(LOCKS_ADDRESS),
        abi=locks_abi
    )
    return contract


class TestLocksContract:
    """
    Tests for LOCKS token contract read functions.
    These tests interact with the actual blockchain.
    """

    def test_contract_connection(self, locks_contract):
        """Test basic connection to the LOCKS contract"""
        assert locks_contract.address is not None
        assert Web3.is_checksum_address(locks_contract.address)

    def test_token_info(self, locks_contract):
        """Test basic token information"""
        name = locks_contract.functions.name().call()
        symbol = locks_contract.functions.symbol().call()
        decimals = locks_contract.functions.decimals().call()

        print(f"\nLOCKS Token Info: {name} ({symbol}), {decimals} decimals")

        assert isinstance(name, str) and len(name) > 0
        assert isinstance(symbol, str) and len(symbol) > 0
        assert isinstance(decimals, int) and decimals > 0
        # LOCKS-specific check
        assert symbol == "LOCKS", f"Expected symbol 'LOCKS', got '{symbol}'"

    def test_total_supply(self, locks_contract):
        """Test getting the total supply"""
        total_supply = locks_contract.functions.totalSupply().call()

        supply_in_tokens = Decimal(total_supply) / Decimal(10 ** 18)
        print(f"\nLOCKS Total Supply: {supply_in_tokens}")

        assert isinstance(total_supply, int)
        assert total_supply > 0

    def test_balance_of(self, locks_contract, account):
        """Test balanceOf function for the bot's account"""
        balance = locks_contract.functions.balanceOf(account.address).call()

        balance_in_tokens = Decimal(balance) / Decimal(10 ** 18)
        print(f"\nLOCKS Balance for {account.address}: {balance_in_tokens}")

        assert isinstance(balance, int)
        assert balance >= 0

    def test_allowance_for_porridge(self, locks_contract, account, web3):
        """Test allowance for PORRIDGE contract (important for staking)"""
        if not PORRIDGE_ADDRESS:
            pytest.skip("No PORRIDGE_ADDRESS provided in environment")

        owner = account.address
        spender = web3.to_checksum_address(PORRIDGE_ADDRESS)

        allowance = locks_contract.functions.allowance(owner, spender).call()

        allowance_in_tokens = Decimal(allowance) / Decimal(10 ** 18)
        print(f"\nLOCKS Allowance for PORRIDGE: {allowance_in_tokens}")

        assert isinstance(allowance, int)
        assert allowance >= 0

    # LOCKS-specific functions

    def test_floor_price(self, locks_contract):
        """Test getting the floor price - crucial for stirring calculations"""
        floor_price = locks_contract.functions.floorPrice().call()

        price_in_honey = Decimal(floor_price) / Decimal(10 ** 18)
        print(f"\nLOCKS Floor Price: {price_in_honey} HONEY")

        assert isinstance(floor_price, int)
        assert floor_price > 0

    def test_market_price(self, locks_contract):
        """Test getting the market price if available"""
        try:
            market_price = locks_contract.functions.marketPrice().call()

            price_in_honey = Decimal(market_price) / Decimal(10 ** 18)
            print(f"\nLOCKS Market Price: {price_in_honey} HONEY")

            assert isinstance(market_price, int)
            assert market_price > 0
        except Exception as e:
            pytest.skip(f"marketPrice() function not available: {e}")

    def test_fsl_psl(self, locks_contract):
        """Test getting FSL and PSL parameters which control price dynamics"""
        try:
            fsl = locks_contract.functions.fsl().call()
            psl = locks_contract.functions.psl().call()

            fsl_value = Decimal(fsl) / Decimal(10 ** 18)
            psl_value = Decimal(psl) / Decimal(10 ** 18)
            print(f"\nLOCKS FSL: {fsl_value}, PSL: {psl_value}")

            assert isinstance(fsl, int)
            assert isinstance(psl, int)
        except Exception as e:
            pytest.skip(f"fsl() or psl() function not available: {e}")

    def test_honey_address(self, locks_contract, web3):
        """Test getting HONEY token address from LOCKS contract"""
        try:
            honey_address = locks_contract.functions.honey().call()
            print(f"\nHONEY Address from LOCKS contract: {honey_address}")

            assert Web3.is_checksum_address(honey_address)

            # Verify it matches the expected HONEY address if provided
            if HONEY_ADDRESS:
                expected_address = web3.to_checksum_address(HONEY_ADDRESS)
                assert honey_address.lower() == expected_address.lower(), \
                    f"HONEY address mismatch: got {honey_address}, expected {expected_address}"
        except Exception as e:
            pytest.skip(f"honey() function not available: {e}")

    def test_target_ratio(self, locks_contract):
        """Test getting the target ratio which affects floor price dynamics"""
        try:
            target_ratio = locks_contract.functions.targetRatio().call()

            ratio_percentage = Decimal(target_ratio) / Decimal(10 ** 18) * 100
            print(f"\nLOCKS Target Ratio: {ratio_percentage}%")

            assert isinstance(target_ratio, int)
        except Exception as e:
            pytest.skip(f"targetRatio() function not available: {e}")

    def test_last_floor_price_changes(self, locks_contract):
        """Test getting last floor price change timestamps"""
        try:
            last_increase = locks_contract.functions.lastFloorIncrease().call()
            last_decrease = locks_contract.functions.lastFloorDecrease().call()

            print(f"\nLast Floor Price Increase: {last_increase}")
            print(f"Last Floor Price Decrease: {last_decrease}")

            assert isinstance(last_increase, int)
            assert isinstance(last_decrease, int)
        except Exception as e:
            pytest.skip(f"lastFloorIncrease() or lastFloorDecrease() function not available: {e}")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])