"""
Main execution module for the Goldilocks DeFi bot.
Coordinates the protocol interaction cycle.
"""
import asyncio
import sys

import config
from web3_utils import ACCOUNT
from honey_logic import get_honey_balance
from locks_logic import swap_honey_to_locks
from porridge_logic import (
    borrow_if_possible, 
    claim_porridge, 
    stir_porridge, 
    stake_all_locks
)
from notifications import send_discord_message, EventMessageCollector


async def run_protocol_cycle():
    """
    Run a single protocol cycle: borrow → claim → stir → swap → stake.

    Returns:
        Success status
    """
    event_collector = EventMessageCollector()

    # Step 1: Borrow if possible
    can_borrow, borrowed_amount = await borrow_if_possible()
    if not can_borrow:
        return False  # Skip the rest of the cycle

    event_collector.add_success(f"Borrowed {borrowed_amount / 10 ** 18:.4f} HONEY")

    # Step 2: Claim PORRIDGE
    try:
        claimed_amount = await claim_porridge()
        if claimed_amount > 0:
            event_collector.add_success(f"Claimed {claimed_amount / 10 ** 18:.4f} PORRIDGE")
        else:
            event_collector.add_info("No PORRIDGE to claim")
    except Exception as e:
        print(f"Error claiming PORRIDGE: {e}")
        event_collector.add_error(f"Claim PORRIDGE failed: {str(e)[:100]}")

    # Step 3: Stir PORRIDGE
    honey_used = 0  # Track how much HONEY was used for stirring
    try:
        stir_ok, leftover_prg, honey_used, stir_percentage = await stir_porridge(borrowed_amount)
        if stir_ok:
            if stir_percentage == 100:
                event_collector.add_success(f"Stirred 100% of PORRIDGE using {honey_used / 10 ** 18:.4f} HONEY")
            else:
                event_collector.add_warning(
                    f"Stirred ~{stir_percentage}% of PORRIDGE using {honey_used / 10 ** 18:.4f} HONEY")
        else:
            event_collector.add_error("Not enough HONEY to stir PORRIDGE")
    except Exception as e:
        print(f"Error stirring PORRIDGE: {e}")
        event_collector.add_error(f"Stir transaction failed: {str(e)[:100]}")

    # Step 4: Swap leftover HONEY (if enabled)
    if config.SWAP_LEFTOVER_HONEY:
        try:
            swapped = await swap_honey_to_locks(borrowed_amount, honey_used)
            if swapped > 0:
                event_collector.add_success(f"Swapped leftover {swapped / 10 ** 18:.4f} HONEY to LOCKS")
        except Exception as e:
            print(f"Error swapping HONEY: {e}")
            event_collector.add_error(f"HONEY swap failed: {str(e)[:100]}")

    # Step 5: Stake LOCKS
    try:
        staked = await stake_all_locks()
        if staked:
            event_collector.add_success("Staked LOCKS")
    except Exception as e:
        print(f"Error staking LOCKS: {e}")
        event_collector.add_error(f"Staking failed: {str(e)[:100]}")

    # Send cycle summary to Discord
    event_collector.send()

    return True


async def main_loop():
    """
    Main bot loop. Runs protocol cycles at specified intervals.
    """
    print(f"Bot starting with account {ACCOUNT.address}")
    print(f"BORROW_THRESHOLD: {config.BORROW_THRESHOLD / 10 ** 18:.4f} HONEY")
    print(f"ALLOW_WALLET_HONEY: {config.ALLOW_WALLET_HONEY}")
    print(f"SWAP_LEFTOVER_HONEY: {config.SWAP_LEFTOVER_HONEY}")
    print(f"SWAP_ALL_WALLET_HONEY: {config.SWAP_ALL_WALLET_HONEY}")
    print(f"CYCLE_INTERVAL: {config.CYCLE_INTERVAL} seconds")

    # Initial notification
    send_discord_message(f"🤖 Goldilocks bot started with account {ACCOUNT.address[:6]}...{ACCOUNT.address[-4:]}")

    while True:
        try:
            print(f"\n--- New cycle starting ---")

            # Run protocol cycle
            success = await run_protocol_cycle()

            # If cycle was skipped, log reason
            if not success:
                print(f"Cycle skipped. Waiting {config.CYCLE_INTERVAL} seconds...")
            else:
                print(f"Cycle complete. Waiting {config.CYCLE_INTERVAL} seconds...")

        except Exception as e:
            error_msg = f"❌ Main loop error: {str(e)[:200]}"
            print(error_msg)
            send_discord_message(error_msg)

        # Wait for next cycle
        await asyncio.sleep(config.CYCLE_INTERVAL)


if __name__ == "__main__":
    try:
        # Check initial balances
        get_honey_balance()
        
        # Run main loop
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Bot stopped by user")
        send_discord_message("🛑 Bot stopped by user")
    except Exception as e:
        error_msg = f"❌ Critical error: {str(e)}"
        print(error_msg)
        send_discord_message(error_msg)
        sys.exit(1)
async def main_loop():
    """
    Main bot loop. Runs protocol cycles at specified intervals.
    """
    print(f"Bot starting with account {ACCOUNT.address}")
    print(f"BORROW_THRESHOLD: {config.BORROW_THRESHOLD / 10**18:.4f} HONEY")
    print(f"ALLOW_WALLET_HONEY: {config.ALLOW_WALLET_HONEY}")
    print(f"SWAP_LEFTOVER_HONEY: {config.SWAP_LEFTOVER_HONEY}")
    print(f"CYCLE_INTERVAL: {config.CYCLE_INTERVAL} seconds")

    # Initial notification
    send_discord_message(f"🤖 Goldilocks bot started with account {ACCOUNT.address[:6]}...{ACCOUNT.address[-4:]}")

    while True:
        try:
            print(f"\n--- New cycle starting ---")

            # Run protocol cycle
            success = await run_protocol_cycle()

            # If cycle was skipped, log reason
            if not success:
                print(f"Cycle skipped. Waiting {config.CYCLE_INTERVAL} seconds...")
            else:
                print(f"Cycle complete. Waiting {config.CYCLE_INTERVAL} seconds...")

        except Exception as e:
            error_msg = f"❌ Main loop error: {str(e)[:200]}"
            print(error_msg)
            send_discord_message(error_msg)

        # Wait for next cycle
        await asyncio.sleep(config.CYCLE_INTERVAL)