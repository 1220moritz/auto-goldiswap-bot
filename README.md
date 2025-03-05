# Auto Goldiswap Bot

An automated bot for maximizing yield on the Goldilocks DAO's Goldiswap protocol through borrowing, claiming, stirring, and staking.

## Overview

This bot automates the following actions on the Goldiswap protocol:

1. **Borrow**: Checks your borrow limit and borrows HONEY if above threshold
2. **Claim**: Claims accrued PORRIDGE rewards
3. **Stir**: Combines PORRIDGE and HONEY to mint LOCKS at floor price
4. **Swap**: Optionally swaps leftover HONEY to LOCKS (at market price)
5. **Stake**: Stakes all LOCKS to earn more PORRIDGE

The bot runs in cycles and sends progress updates to Discord.

## What is Goldiswap?

Goldiswap is a novel AMM developed by Goldilocks DAO for Berachain that governs the supply, price, and behavior of LOCKS, the DAO's governance token. It features:

- An up-only floor price mechanism for LOCKS tokens
- Interest-free borrowing against staked LOCKS
- No liquidation risk or price impact when borrowing

To learn more about Goldiswap, visit:
- [Official Website](https://www.goldilocksdao.io/goldiswap/)
- [Documentation](https://goldilocks.gitbook.io/docs/goldiswap/overview)

## Prerequisites

- Python 3.9 or higher ([How to install Python](https://www.python.org/downloads/))
- A wallet with some staked LOCKS (to have borrowing power)
- Access to a [Berachain RPC](https://docs.berachain.com/developers/developer-tools#rpc-infrastructure-providers)
- A Discord webhook URL for notifications

## Installation

### Step 1: Install Python

If you don't have Python installed:

- **Windows**: Download and run the installer from [python.org](https://www.python.org/downloads/windows/)
  - Make sure to check "Add Python to PATH" during installation
- **macOS**: Download from [python.org](https://www.python.org/downloads/macos/) or use Homebrew: `brew install python`
- **Linux**: Use your package manager, e.g., `sudo apt install python3 python3-pip` for Ubuntu

Verify your installation by opening a terminal or command prompt and running:
```
python --version
```

### Step 2: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/1220moritz/auto-goldiswap-bot.git
cd auto-goldiswap-bot
```

If you don't have Git installed, you can download the code as a ZIP file from the repository and extract it.

### Step 3: Set Up a Virtual Environment

A virtual environment isolates the bot's dependencies from your global Python installation:

```bash
# in the auto-goldiswap-bot folder
# Create a virtual environment
python -m venv .

# Activate the virtual environment
# On Windows:
Scripts\activate
# On macOS/Linux:
source bin/activate
```

Your command prompt should now show `(auto-goldiswap-bot)` at the beginning, indicating the virtual environment is active.

### Step 4: Install Dependencies

With the virtual environment active, install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

### Step 1: Create a .env File

Copy the `env-demo` to `.env` via   
```bash
cp env-demo .env
```
or create a file named `.env` in the project root directory with the following structure:

```
# Required configuration
RPC_URL=https://rpc.berachain.com  # Replace with your RPC endpoint
PRIVATE_KEY=your_private_key_here_without_0x_prefix
WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_id/your_webhook_token

# Contract addresses
HONEY_ADDRESS=0xfcbd14dc51f0a4d49d5e53c2e0950e0bc26d0dce
LOCKS_ADDRESS=0xb7e448e5677d212b8c8da7d6312e8afc49800466
PORRIDGE_ADDRESS=0xbf2e152f460090ace91a456e3dee5acf703f27ad

# Optional configuration
BORROW_THRESHOLD=1000000000000000000  # 1 token with 18 decimals
ALLOW_WALLET_HONEY=false  # Set to true to use wallet HONEY if borrowed amount isn't enough
SWAP_LEFTOVER_HONEY=true  # Set to true to swap leftover HONEY to LOCKS
SWAP_ALL_WALLET_HONEY=false  # Set to true to swap ALL wallet HONEY instead of just leftover borrowed HONEY
CYCLE_INTERVAL=120  # Time between cycles in seconds
```

### Step 2: Configure Contract Addresses (if they are outdated)

Replace the contract addresses with the correct ones for the Goldiswap protocol:

```
HONEY_ADDRESS=0x...  # HONEY token address
LOCKS_ADDRESS=0x...  # LOCKS token address
PORRIDGE_ADDRESS=0x...  # PORRIDGE contract address
```

### Step 3: Add Your Wallet and RPC Details

1. **RPC_URL**: Get an RPC URL for Berachain from a provider or use the official Berachain RPC
2. **PRIVATE_KEY**: Your wallet's private key (without the '0x' prefix)
   - ⚠️ **IMPORTANT**: Keep your private key secure and never share it
   - Use a dedicated wallet with limited funds for bot operation

### Step 4: Set Up Discord Notifications

1. Create a Discord server or use an existing one
2. In a channel's settings, go to "Integrations" → "Webhooks" → "New Webhook". Use [this video](https://www.youtube.com/watch?v=fKksxz2Gdnc) if you need additional help.
3. Copy the webhook URL and paste it as `WEBHOOK_URL` in your .env file

## Running the Bot

### Starting the Bot

With your virtual environment activated:

```bash
# Navigate to the src directory if needed
cd src

# Run the bot
python main.py
```

The bot will:
1. Initialize and connect to the blockchain
2. Display your configuration settings
3. Send an initial notification to Discord
4. Start running cycles automatically

### Monitoring

The bot provides:
- Console logs showing all actions and transactions
- Discord notifications for each active cycle
- Transaction links in the console logs

### Stopping the Bot

To stop the bot, press `Ctrl+C` in the terminal. The bot will send a shutdown notification to Discord.

## Configuration Options

- **BORROW_THRESHOLD**: Minimum amount of HONEY to borrow in wei (this avoid looping as the bot doesn't try to borrow minimal amounts)
- **ALLOW_WALLET_HONEY**: If true, uses extra HONEY from wallet for stirring when borrowed HONEY isn't enough
- **SWAP_LEFTOVER_HONEY**: If true, swaps leftover borrowed HONEY to LOCKS after stirring
- **SWAP_ALL_WALLET_HONEY**: If true, swaps all wallet HONEY instead of just leftover borrowed HONEY. Be careful as this can be really annoying!
- **CYCLE_INTERVAL**: Time in seconds between cycles

## Directory Structure

```
auto-goldiswap-bot/
├── ABIs/                  # Contract ABIs
│   ├── abi_honey.json
│   ├── abi_locks.json
│   └── abi_porridge.json
├── src/                   # Source code
│   ├── config.py          # Configuration module
│   ├── contracts.py       # Contract initialization
│   ├── honey_logic.py     # HONEY token operations
│   ├── locks_logic.py     # LOCKS token operations
│   ├── main.py            # Main execution module
│   ├── notifications.py   # Discord notifications
│   ├── porridge_logic.py  # PORRIDGE operations
│   └── web3_utils.py      # Web3 utilities
├── .env                   # Environment variables (create this)
├── .gitignore             # Git ignore file
├── README.md              # This file
└── requirements.txt       # Python dependencies
```

## Troubleshooting

### Common Issues

1. **"Transaction reverted" errors**:
   - Check your account has enough funds for gas
   - Ensure the contract addresses are correct
   - Verify you have borrowing power (staked LOCKS)
   - Check if this happens every cycle or just was an exception

2. **Gas estimation failures**:
   - The bot uses fallback gas values when estimation fails
   - If transactions consistently fail, try increasing the fallback gas values in `web3_utils.py`

3. **RPC connection issues**:
   - Try a different RPC provider
   - Check your internet connection
   - Verify the RPC URL is correct

4. **Bot not borrowing**:
   - Make sure you have staked LOCKS to have borrowing power
   - Check the `BORROW_THRESHOLD` isn't set too high

### Getting Help

For more help with the Goldilocks protocol, join the official community channels:
- [Discord](https://discord.gg/goldilocks)
- [Official Documentation](https://goldilocks.gitbook.io/docs/)
   
or just message [me on Discord](https://discord.com/users/713118695165263923)

## Security Considerations

- Use a dedicated wallet with limited funds
- Never share your private key
- Test with small amounts before running with large amounts
- Monitor the bot regularly

## Donations

If dis bot helps u to make sum money, maybe u wanna share sum of it.
```
0x2D438b5F9dBb11fB406a92Fd97476f4Cdc9947D1
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
