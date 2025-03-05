"""
PORRIDGE token logic for the Goldilocks DeFi bot.
Handles PORRIDGE token and staking/borrowing operations.
"""
import config
from web3_utils import ACCOUNT, send_tx, approve_if_needed, format_amount
from contracts import porridge_contract
from honey_logic import check_honey_for_stir
from locks_logic import get_floor_price, calculate_stirable_porridge


def get_porridge_balance():
    """
    Get PORRIDGE balance for the bot's account.
    
    Returns:
        Current PORRIDGE balance
    """
    balance = porridge_contract.functions.balanceOf(ACCOUNT.address).call()
    print(f"PORRIDGE balance: {format_amount(balance)} PORRIDGE")
    return balance


def get_claimable_porridge():
    """
    Get claimable PORRIDGE for the bot's account.
    
    Returns:
        Amount of claimable PORRIDGE
    """
    claimable = porridge_contract.functions.userClaimablePrg(ACCOUNT.address).call()
    print(f"Claimable PORRIDGE: {format_amount(claimable)} PORRIDGE")
    return claimable


def get_borrow_limit():
    """
    Get the current borrow limit for the bot's account.
    
    Returns:
        Current borrow limit
    """
    limit = porridge_contract.functions.userBorrowLimit(ACCOUNT.address).call()
    print(f"User borrow limit: {format_amount(limit)} HONEY")
    return limit


def get_borrowed_honey():
    """
    Get the amount of HONEY borrowed by the bot's account.
    
    Returns:
        Amount of borrowed HONEY
    """
    borrowed = porridge_contract.functions.userBorrowedHoney(ACCOUNT.address).call()
    print(f"Borrowed HONEY: {format_amount(borrowed)} HONEY")
    return borrowed


def get_staked_locks():
    """
    Get the amount of LOCKS staked by the bot's account.
    
    Returns:
        Amount of staked LOCKS
    """
    staked = porridge_contract.functions.userStakedLocks(ACCOUNT.address).call()
    print(f"Staked LOCKS: {format_amount(staked)} LOCKS")
    return staked


async def borrow_if_possible():
    """
    Check borrowing limit and borrow if above threshold.
    
    Returns:
        (success, borrowed_amount)
    """
    try:
        # Check user's borrow limit
        limit = get_borrow_limit()

        # Skip if below threshold
        if limit < config.BORROW_THRESHOLD:
            print(f"Borrow limit below threshold ({format_amount(config.BORROW_THRESHOLD)} HONEY), skipping this cycle")
            return False, 0

        # Execute borrow
        print(f"Borrowing {format_amount(limit)} HONEY")
        receipt = await send_tx(porridge_contract.functions.borrow(limit))

        # Get the borrowed amount from the receipt events
        borrowed_amount = 0
        for log in receipt.logs:
            # Try to parse as Borrow event
            try:
                event = porridge_contract.events.Borrow().process_log(log)
                borrowed_amount = event.args.amount
                break
            except:
                continue

        # If we couldn't get from events, use the limit as approximation
        if borrowed_amount == 0:
            borrowed_amount = limit

        print(f"Successfully borrowed {format_amount(borrowed_amount)} HONEY")
        return True, borrowed_amount
    except Exception as e:
        print(f"Error in borrow_if_possible: {e}")
        raise


async def claim_porridge():
    """
    Claim accrued PORRIDGE rewards.
    
    Returns:
        Amount of PORRIDGE claimed
    """
    try:
        # Get claimable amount before claiming
        claimable = get_claimable_porridge()

        if claimable == 0:
            print("No PORRIDGE to claim")
            return 0

        print("Claiming PORRIDGE rewards")
        receipt = await send_tx(porridge_contract.functions.claim())

        # Get the claimed amount from receipt events
        claimed_amount = 0
        for log in receipt.logs:
            try:
                event = porridge_contract.events.Claim().process_log(log)
                claimed_amount = event.args.amount
                break
            except:
                continue

        # If we couldn't get from events, use the claimable as approximation
        if claimed_amount == 0:
            claimed_amount = claimable

        print(f"Successfully claimed {format_amount(claimed_amount)} PORRIDGE")
        return claimed_amount
    except Exception as e:
        print(f"Error in claim_porridge: {e}")
        raise


async def stir_porridge(borrowed_honey):
    """
    Stir PORRIDGE with HONEY to get LOCKS.
    
    Args:
        borrowed_honey: Amount of HONEY borrowed in this cycle
        
    Returns:
        (success, leftover_porridge, honey_used, stir_percentage)
    """
    try:
        # Get current balances
        prg_balance = get_porridge_balance()
        if prg_balance == 0:
            print("No PORRIDGE to stir")
            return False, 0, 0, 0

        # Calculate HONEY needed for stirring all PORRIDGE
        floor_price = get_floor_price()
        needed_honey_full = (floor_price * prg_balance) // (10 ** 18)
        print(f"Needed HONEY for full stir: {format_amount(needed_honey_full)} HONEY")

        # Check HONEY availability and determine strategy
        honey_to_use, can_stir_full, using_wallet_honey = check_honey_for_stir(needed_honey_full, borrowed_honey)

        if honey_to_use == 0:
            print("No HONEY available for stirring")
            return False, prg_balance, 0, 0

        # Determine how much to stir
        if can_stir_full:
            # Can stir all PORRIDGE
            stir_amount = prg_balance
            honey_used = needed_honey_full
            stir_percentage = 100
        else:
            # Calculate how much PORRIDGE can be stirred with available HONEY
            stirable_prg = calculate_stirable_porridge(honey_to_use, floor_price)

            if stirable_prg == 0:
                print("Not enough HONEY to stir even 1 PORRIDGE")
                return False, prg_balance, needed_honey_full, 0

            stir_amount = min(stirable_prg, prg_balance)
            honey_used = (floor_price * stir_amount) // (10 ** 18)
            stir_percentage = (stir_amount * 100) // prg_balance

        # Print strategy details
        wallet_msg = " (including wallet HONEY)" if using_wallet_honey else ""
        print(f"Stirring {format_amount(stir_amount)} PORRIDGE ({stir_percentage}%) "
              f"using {format_amount(honey_used)} HONEY{wallet_msg}")

        # Approve tokens for stirring
        await approve_if_needed(honey_contract, config.PORRIDGE_ADDRESS, honey_used)
        await approve_if_needed(porridge_contract, config.PORRIDGE_ADDRESS, stir_amount)

        # Execute stir
        receipt = await send_tx(porridge_contract.functions.stir(stir_amount))

        # Check stir event for confirmation
        stirred_amount = 0
        for log in receipt.logs:
            try:
                event = porridge_contract.events.Stir().process_log(log)
                stirred_amount = event.args.amount
                break
            except:
                continue

        if stirred_amount > 0:
            print(f"Successfully stirred {format_amount(stirred_amount)} PORRIDGE")
        else:
            print(f"Stir transaction confirmed, but couldn't verify amount from events")

        # Return success, leftover PORRIDGE, honey used, and stir percentage
        leftover_prg = prg_balance - stir_amount
        return True, leftover_prg, honey_used, stir_percentage
    except Exception as e:
        print(f"Error in stir_porridge: {e}")
        raise


async def stake_all_locks():
    """
    Stake all LOCKS in the porridge contract.
    
    Returns:
        Success status
    """
    try:
        locks_balance = locks_contract.functions.balanceOf(ACCOUNT.address).call()
        if locks_balance == 0:
            print("No LOCKS to stake")
            return False

        print(f"Staking {format_amount(locks_balance)} LOCKS")

        # Approve LOCKS for porridge contract
        await approve_if_needed(locks_contract, config.PORRIDGE_ADDRESS, locks_balance)

        # Execute stake
        receipt = await send_tx(porridge_contract.functions.stake(locks_balance))

        # Check stake event for confirmation
        staked_amount = 0
        for log in receipt.logs:
            try:
                event = porridge_contract.events.Stake().process_log(log)
                staked_amount = event.args.amount
                break
            except:
                continue

        if staked_amount > 0:
            print(f"Successfully staked {format_amount(staked_amount)} LOCKS")
        else:
            print(f"Stake transaction confirmed, but couldn't verify amount from events")

        return True
    except Exception as e:
        print(f"Error in stake_all_locks: {e}")
        raise


# Fix circular import issues by importing here
from contracts import honey_contract, locks_contract
