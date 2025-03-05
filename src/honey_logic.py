"""
HONEY token logic for the Goldilocks DeFi bot.
Handles HONEY token related operations.
"""
import config
from web3_utils import ACCOUNT, format_amount
from contracts import honey_contract


def get_honey_balance():
    """
    Get HONEY balance for the bot's account.
    
    Returns:
        Current HONEY balance
    """
    balance = honey_contract.functions.balanceOf(ACCOUNT.address).call()
    print(f"HONEY balance: {format_amount(balance)} HONEY")
    return balance


def get_honey_allowance(spender):
    """
    Get HONEY allowance for a specific address.
    
    Args:
        spender: Address to check allowance for
        
    Returns:
        Current allowance
    """
    allowance = honey_contract.functions.allowance(ACCOUNT.address, spender).call()
    print(f"HONEY allowance for {spender}: {format_amount(allowance)}")
    return allowance


def check_honey_for_stir(needed_amount, borrowed_amount):
    """
    Check if we have enough HONEY for stirring and determine strategy.
    
    Args:
        needed_amount: Amount of HONEY needed for full stir
        borrowed_amount: Amount of HONEY that was borrowed in this cycle
        
    Returns:
        (honey_to_use, can_stir_full, use_wallet_honey)
    """
    honey_balance = get_honey_balance()
    
    if borrowed_amount >= needed_amount:
        # Can stir all PORRIDGE
        return needed_amount, True, False
    
    # Need to do partial stir or skip based on settings
    if not config.ALLOW_WALLET_HONEY:
        # Only use borrowed honey
        honey_available = min(honey_balance, borrowed_amount)
    else:
        # Use all available honey
        honey_available = honey_balance
        
    return honey_available, False, config.ALLOW_WALLET_HONEY and honey_available > borrowed_amount
