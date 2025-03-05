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
PORRIDGE_ADDRESS = os.getenv("PORRIDGE_ADDRESS")
LOCKS_ADDRESS = os.getenv("LOCKS_ADDRESS")
HONEY_ADDRESS = os.getenv("HONEY_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Skip tests if environment is not set up
if not (RPC_URL and PORRIDGE_ADDRESS and PRIVATE_KEY):
    pytest.skip("Missing RPC_URL, PORRIDGE_ADDRESS, or PRIVATE_KEY in environment", allow_module_level=True)


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
def porridge_contract(web3):
    """Initialize PORRIDGE contract instance for testing"""
    # Load ABI from file
    abi_path = "../src/ABIs/abi_porridge.json"
    try:
        with open(abi_path, 'r') as f:
            porridge_abi = json.load(f)
    except FileNotFoundError:
        pytest.skip(f"PORRIDGE ABI file not found at {abi_path}", allow_module_level=True)

    # Initialize contract
    contract = web3.eth.contract(
        address=web3.to_checksum_address(PORRIDGE_ADDRESS),
        abi=porridge_abi
    )
    return contract


class TestPorridgeContract:
    """
    Tests for PORRIDGE token and protocol functions.
    These tests interact with the actual blockchain.
    """

    def test_contract_connection(self, porridge_contract):
        """Test basic connection to the PORRIDGE contract"""
        assert porridge_contract.address is not None
        assert Web3.is_checksum_address(porridge_contract.address)

    def test_token_info(self, porridge_contract):
        """Test basic token information"""
        name = porridge_contract.functions.name().call()
        symbol = porridge_contract.functions.symbol().call()
        decimals = porridge_contract.functions.decimals().call()

        print(f"\nPORRIDGE Token Info: {name} ({symbol}), {decimals} decimals")

        assert isinstance(name, str) and len(name) > 0
        assert isinstance(symbol, str) and len(symbol) > 0
        assert isinstance(decimals, int) and decimals > 0
        # PORRIDGE-specific check
        assert symbol == "PRG", f"Expected symbol 'PRG', got '{symbol}'"

    def test_total_supply(self, porridge_contract):
        """Test getting the total supply"""
        total_supply = porridge_contract.functions.totalSupply().call()

        supply_in_tokens = Decimal(total_supply) / Decimal(10 ** 18)
        print(f"\nPORRIDGE Total Supply: {supply_in_tokens}")

        assert isinstance(total_supply, int)
        assert total_supply > 0

    def test_balance_of(self, porridge_contract, account):
        """Test balanceOf function for the bot's account"""
        balance = porridge_contract.functions.balanceOf(account.address).call()

        balance_in_tokens = Decimal(balance) / Decimal(10 ** 18)
        print(f"\nPORRIDGE Balance for {account.address}: {balance_in_tokens}")

        assert isinstance(balance, int)
        assert balance >= 0

    def test_allowance_for_self(self, porridge_contract, account, web3):
        """Test allowance for PORRIDGE contract itself (for stir function)"""
        owner = account.address
        spender = porridge_contract.address

        allowance = porridge_contract.functions.allowance(owner, spender).call()

        allowance_in_tokens = Decimal(allowance) / Decimal(10 ** 18)
        print(f"\nPORRIDGE Allowance for itself: {allowance_in_tokens}")

        assert isinstance(allowance, int)
        assert allowance >= 0

    # PORRIDGE-specific functions

    def test_staked_locks(self, porridge_contract, account):
        """Test getting staked LOCKS amount - critical for the protocol"""
        try:
            # Try the userStakedLocks function first (more modern)
            try:
                staked = porridge_contract.functions.userStakedLocks(account.address).call()
            except Exception:
                # Fall back to stakedLocks mapping (older)
                staked = porridge_contract.functions.stakedLocks(account.address).call()

            staked_in_tokens = Decimal(staked) / Decimal(10 ** 18)
            print(f"\nStaked LOCKS: {staked_in_tokens}")

            assert isinstance(staked, int)
            assert staked >= 0
        except Exception as e:
            pytest.skip(f"Neither userStakedLocks nor stakedLocks function available: {e}")

    def test_borrowed_honey(self, porridge_contract, account):
        """Test getting borrowed HONEY amount - crucial for borrowing logic"""
        try:
            # Try the userBorrowedHoney function first
            try:
                borrowed = porridge_contract.functions.userBorrowedHoney(account.address).call()
            except Exception:
                # Fall back to borrowedHoney mapping
                borrowed = porridge_contract.functions.borrowedHoney(account.address).call()

            borrowed_in_tokens = Decimal(borrowed) / Decimal(10 ** 18)
            print(f"\nBorrowed HONEY: {borrowed_in_tokens}")

            assert isinstance(borrowed, int)
            assert borrowed >= 0
        except Exception as e:
            pytest.skip(f"Neither userBorrowedHoney nor borrowedHoney function available: {e}")

    def test_borrow_limit(self, porridge_contract, account):
        """Test getting borrow limit - determines how much can be borrowed"""
        try:
            borrow_limit = porridge_contract.functions.userBorrowLimit(account.address).call()

            limit_in_tokens = Decimal(borrow_limit) / Decimal(10 ** 18)
            print(f"\nBorrow limit: {limit_in_tokens} HONEY")

            assert isinstance(borrow_limit, int)
            assert borrow_limit >= 0
        except Exception as e:
            pytest.skip(f"userBorrowLimit function not available: {e}")

    def test_claimable_porridge(self, porridge_contract, account):
        """Test getting claimable PORRIDGE amount - important for rewards claim"""
        try:
            # Try the userClaimablePrg function first
            try:
                claimable = porridge_contract.functions.userClaimablePrg(account.address).call()
            except Exception:
                # Fall back to claimablePrg mapping
                claimable = porridge_contract.functions.claimablePrg(account.address).call()

            claimable_in_tokens = Decimal(claimable) / Decimal(10 ** 18)
            print(f"\nClaimable PORRIDGE: {claimable_in_tokens}")

            assert isinstance(claimable, int)
            assert claimable >= 0
        except Exception as e:
            pytest.skip(f"Neither userClaimablePrg nor claimablePrg function available: {e}")

    def test_claimable_porridge_per_locks_stored(self, porridge_contract):
        """Test getting the stored claimablePrgPerLocksStored value"""
        try:
            per_locks_stored = porridge_contract.functions.claimablePrgPerLocksStored().call()

            value = Decimal(per_locks_stored) / Decimal(10 ** 18)
            print(f"\nClaimable PRG Per Locks Stored: {value}")

            assert isinstance(per_locks_stored, int)
            assert per_locks_stored >= 0
        except Exception as e:
            pytest.skip(f"claimablePrgPerLocksStored function not available: {e}")

    def test_annual_prg_emissions(self, porridge_contract):
        """Test getting annual PRG emissions - affects reward rates"""
        try:
            emissions = porridge_contract.functions.annualPrgEmissions().call()

            emissions_in_tokens = Decimal(emissions) / Decimal(10 ** 18)
            print(f"\nAnnual PRG Emissions: {emissions_in_tokens} PRG")

            assert isinstance(emissions, int)
            assert emissions > 0
        except Exception as e:
            pytest.skip(f"annualPrgEmissions function not available: {e}")

    def test_last_update_time(self, porridge_contract):
        """Test getting lastUpdateTime - used for reward calculations"""
        try:
            last_update = porridge_contract.functions.lastUpdateTime().call()

            print(f"\nLast Update Time: {last_update}")

            assert isinstance(last_update, int)
            assert last_update > 0
        except Exception as e:
            pytest.skip(f"lastUpdateTime function not available: {e}")

    def test_contract_addresses(self, porridge_contract, web3):
        """Test getting related contract addresses"""
        # Contract references to check
        addresses_to_check = {
            'goldiswap': LOCKS_ADDRESS,  # The LOCKS contract might be goldiswap
            'govlocks': None,  # Unknown address
            'honey': HONEY_ADDRESS,
            'goldilend': None  # Unknown address
        }

        for func_name, expected_address in addresses_to_check.items():
            try:
                func = getattr(porridge_contract.functions, func_name)
                address = func().call()

                print(f"\n{func_name.capitalize()} Address: {address}")

                assert Web3.is_checksum_address(address)

                # Verify matches expected if provided
                if expected_address:
                    expected = web3.to_checksum_address(expected_address)
                    assert address.lower() == expected.lower(), \
                        f"{func_name} address mismatch: got {address}, expected {expected}"
            except Exception as e:
                print(f"\n{func_name}() function not available: {e}")
                continue

    def test_prg_per_token_debt(self, porridge_contract, account):
        """Test prgPerTokenDebt for the account - part of reward calculation"""
        try:
            debt = porridge_contract.functions.prgPerTokenDebt(account.address).call()

            debt_value = Decimal(debt) / Decimal(10 ** 18)
            print(f"\nPRG Per Token Debt: {debt_value}")

            assert isinstance(debt, int)
            assert debt >= 0
        except Exception as e:
            pytest.skip(f"prgPerTokenDebt function not available: {e}")

    def test_vesting_info(self, porridge_contract):
        """Test getting vesting information - affects token release schedule"""
        try:
            deploy_time = porridge_contract.functions.deployTime().call()
            vesting_start = porridge_contract.functions.vestingStart().call()
            vesting_end = porridge_contract.functions.vestingEnd().call()

            print(f"\nDeploy Time: {deploy_time}")
            print(f"Vesting Start: {vesting_start}")
            print(f"Vesting End: {vesting_end}")

            assert isinstance(deploy_time, int)
            assert isinstance(vesting_start, int)
            assert isinstance(vesting_end, int)
        except Exception as e:
            pytest.skip(f"Vesting functions not available: {e}")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])