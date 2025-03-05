"""
Web3 utility functions for the Goldilocks DeFi bot.
Handles Web3 connection, transaction sending, and receipt handling.
"""
import time
import asyncio
from web3 import Web3
from web3.exceptions import TransactionNotFound

import config

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
if not w3.is_connected():
    raise Exception("Failed to connect to RPC.")

# Setup account from private key
ACCOUNT = w3.eth.account.from_key(config.PRIVATE_KEY)
print(f"Connected to blockchain with account: {ACCOUNT.address}")


async def wait_for_receipt(tx_hash, timeout=120):
    """
    Wait for transaction receipt and return it.
    
    Args:
        tx_hash: Transaction hash
        timeout: Maximum time to wait in seconds
        
    Returns:
        Transaction receipt or raises an exception
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt.status == 1:
                    return receipt
                raise Exception(f"Transaction reverted: {tx_hash.hex()}")
        except TransactionNotFound:
            await asyncio.sleep(1)
    raise Exception(f"Timed out waiting for receipt for tx: {tx_hash.hex()}")


async def send_tx(func, value=0, fallback_gas=500000):
    """
    Send a transaction and wait for receipt.
    Handles functions that can't estimate gas by using a fallback gas value.

    Args:
        func: Contract function to call
        value: ETH value to send (default: 0)
        fallback_gas: Gas limit to use if estimation fails (default: 500000)

    Returns:
        Transaction receipt
    """
    try:
        nonce = w3.eth.get_transaction_count(ACCOUNT.address, 'pending')
        tx_params = {
            'from': ACCOUNT.address,
            'nonce': nonce,
            'gasPrice': int(w3.eth.gas_price * 1.2),  # Add 20% to gas price for faster confirmation
            'value': value
        }

        # Try to estimate gas, fall back to default if it fails
        try:
            gas_est = func.estimateGas(tx_params)
            tx_params['gas'] = int(gas_est * 1.2)  # Add 20% buffer to gas limit
        except Exception as gas_err:
            print(f"Gas estimation failed: {gas_err}. Using fallback gas limit of {fallback_gas}")
            tx_params['gas'] = fallback_gas

        # Build, sign and send transaction
        try:
            tx = func.build_transaction(tx_params)
        except Exception as build_err:
            print(f"Transaction build failed: {build_err}. Trying manual encoding.")

            # If buildTransaction fails, try manual encoding
            # Extract contract and function details
            contract_address = func.address
            fn_name = func._function_identifier
            args = func.args

            # Manually create transaction
            contract = func.contract
            data = contract.encodeABI(fn_name=fn_name, args=args)

            tx = {
                'to': contract_address,
                'from': ACCOUNT.address,
                'data': data,
                'gas': tx_params.get('gas', fallback_gas),
                'gasPrice': tx_params['gasPrice'],
                'nonce': tx_params['nonce'],
                'value': tx_params['value']
            }

        signed = ACCOUNT.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        tx_url = f"https://beratrail.io/tx/0x{tx_hash.hex()}"
        print(f"Transaction sent: {tx_url}")
        return await wait_for_receipt(tx_hash)
    except Exception as e:
        print(f"Transaction error: {e}")
        raise

async def approve_if_needed(token_contract, spender, amount=2**256-1):
    """
    Check allowance and approve if needed.
    
    Args:
        token_contract: Token contract instance
        spender: Address to approve spending for
        amount: Amount to approve, defaults to maxInt256
        
    Returns:
        True if approval was needed and executed, False otherwise
    """
    current = token_contract.functions.allowance(ACCOUNT.address, spender).call()
    if current < amount:
        print(f"Approving {token_contract.address} for {spender} with amount {amount}")
        func = token_contract.functions.approve(spender, amount)
        await send_tx(func)
        print(f"Approval successful")
        return True
    return False


def format_amount(amount, decimals=18):
    """
    Format token amount for display.
    
    Args:
        amount: Token amount in smallest unit
        decimals: Token decimals
        
    Returns:
        Formatted string with token amount
    """
    return f"{amount / (10 ** decimals):.4f}"
