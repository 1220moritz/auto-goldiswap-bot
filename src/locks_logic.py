"""
LOCKS token logic for the Goldilocks DeFi bot.
Handles LOCKS token related operations.
"""
import config
from web3_utils import ACCOUNT, send_tx, approve_if_needed, format_amount
from contracts import locks_contract
from honey_logic import get_honey_balance


def get_locks_balance():
    """
    Get LOCKS balance for the bot's account.
    
    Returns:
        Current LOCKS balance
    """
    balance = locks_contract.functions.balanceOf(ACCOUNT.address).call()
    print(f"LOCKS balance: {format_amount(balance)} LOCKS")
    return balance


def get_floor_price():
    """
    Get the current floor price from the LOCKS contract.
    
    Returns:
        Current floor price (HONEY per LOCKS)
    """
    floor_price = locks_contract.functions.floorPrice().call()
    print(f"Floor price: {format_amount(floor_price)} HONEY per LOCKS")
    return floor_price

def get_market_price():
    """
    Get the current market price from the LOCKS contract.

    Returns:
        Current market price (HONEY per LOCKS)
    """
    market_price = locks_contract.functions.marketPrice().call()
    print(f"Market price: {format_amount(market_price)} HONEY per LOCKS")
    return market_price


def calculate_stirable_porridge(honey_amount, floor_price):
    """
    Calculate how much PORRIDGE can be stirred with a given amount of HONEY.
    
    Args:
        honey_amount: Amount of HONEY available
        floor_price: Current floor price
        
    Returns:
        Amount of PORRIDGE that can be stirred
    """
    if floor_price == 0:
        return 0
        
    stirable_prg = (honey_amount * 10 ** 18) // floor_price
    return stirable_prg


async def swap_honey_to_locks(borrowed_amount=0, honey_used=0):
    """
    Swap leftover HONEY to LOCKS using the locks contract buy function.
    By default, only swaps leftover borrowed HONEY (borrowed_amount - honey_used).
    If SWAP_ALL_WALLET_HONEY is enabled, swaps most of the wallet's HONEY.

    Args:
        borrowed_amount: Amount of HONEY borrowed in this cycle
        honey_used: Amount of HONEY used for stirring in this cycle

    Returns:
        Amount of HONEY swapped or 0 if none
    """
    if not config.SWAP_LEFTOVER_HONEY:
        print("SWAP_LEFTOVER_HONEY is disabled, skipping swap")
        return 0

    try:
        # Determine how much HONEY to swap
        leftover_borrowed = max(0, borrowed_amount - honey_used)

        if config.SWAP_ALL_WALLET_HONEY:
            # Swap 95% of all available HONEY if SWAP_ALL_WALLET_HONEY is enabled
            total_honey = get_honey_balance()
            honey_balance = int(total_honey * 0.95)  # Leave 5% buffer
            print(
                f"SWAP_ALL_WALLET_HONEY is enabled, swapping 95% of wallet HONEY ({format_amount(honey_balance)} of {format_amount(total_honey)})")
        else:
            # Only swap leftover borrowed HONEY
            honey_balance = leftover_borrowed
            print(f"Swapping only leftover borrowed HONEY: {format_amount(honey_balance)}")

        if honey_balance <= 0:
            print("No HONEY to swap")
            return 0

        # Approve HONEY for locks contract
        await approve_if_needed(honey_contract, config.LOCKS_ADDRESS, honey_balance)

        # Get floor price for calculation
        market_price = get_market_price()

        # Estimate LOCKS amount based on floor price and slippage 5%
        locks_amount = int((honey_balance * 10**18) / market_price * 0.95)

        print(f"Buying approximately {format_amount(locks_amount)} LOCKS with max {format_amount(honey_balance)} HONEY")

        # Execute buy
        receipt = await send_tx(locks_contract.functions.buy(locks_amount, honey_balance))

        # Check buy event for confirmation
        swapped_amount = 0
        for log in receipt.logs:
            try:
                event = locks_contract.events.Buy().process_log(log)
                swapped_amount = event.args.amount  # Fixed typo from 'arweb3_utilsgs'
                break
            except:
                continue

        if swapped_amount > 0:
            print(f"Successfully bought {format_amount(swapped_amount)} LOCKS")
        else:
            print(f"Buy transaction confirmed, but couldn't verify amount from events")

        return honey_balance
    except Exception as e:
        print(f"Error in swap_honey_to_locks: {e}")
        raise


# Fix circular import by importing here
from contracts import honey_contract
