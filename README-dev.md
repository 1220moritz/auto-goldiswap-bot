# Auto Goldiswap Bot - Developer Documentation

This documentation provides technical details about the Auto Goldiswap Bot's architecture, operation, and codebase for developers who want to understand or contribute to the project.

## Goldiswap Protocol Overview

Before diving into the bot architecture, it's important to understand the key aspects of the Goldiswap protocol that the bot interacts with:

1. **LOCKS Token**: The governance token for Goldilocks DAO with an up-only floor price mechanism
2. **HONEY Token**: Berachain's native stablecoin used for all operations
3. **PORRIDGE Token**: Earned as rewards for staking LOCKS
4. **Liquidity Pools**: Two main pools - Floor Supporting Liquidity (FSL) and Price Supporting Liquidity (PSL)
5. **Core Operations**:
   - **Borrowing**: Stake LOCKS to borrow HONEY without interest or liquidation risk
   - **Stirring**: Combine PORRIDGE and HONEY to mint LOCKS at floor price
   - **Staking**: Stake LOCKS to earn PORRIDGE rewards

The bot maximizes yield by automatically cycling through these operations. For more detailed protocol information, refer to the [official documentation](https://goldilocks.gitbook.io/docs/goldiswap/overview).

## Architecture Overview

The bot follows a modular architecture with clear separation of concerns:

```
                                ┌─────────────┐
                                │    main     │
                                └──────┬──────┘
                                       │
                     ┌─────────────────┼─────────────────┐
                     │                 │                 │
              ┌──────▼─────┐    ┌──────▼─────┐    ┌──────▼─────┐
              │  honey_    │    │  locks_    │    │ porridge_  │
              │  logic     │    │  logic     │    │ logic      │
              └──────┬─────┘    └──────┬─────┘    └──────┬─────┘
                     │                 │                 │
                     └─────────────────┼─────────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │      contracts      │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │     web3_utils      │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │       config        │
                            └─────────────────────┘
```

The bot operates through asynchronous functions and processes that interact with the Berachain blockchain and the Goldiswap protocol.

## Module Breakdown

### 1. `config.py`
- **Purpose**: Loads and validates environment variables
- **Key Components**:
  - Contract addresses (HONEY, LOCKS, PORRIDGE)
  - Configuration options (BORROW_THRESHOLD, ALLOW_WALLET_HONEY, etc.)
  - Path constants for ABIs
- **Technical Notes**:
  - Environment variables are loaded via dotenv
  - Required variables trigger ValueError if missing
  - Optional variables have sensible defaults

### 2. `web3_utils.py`
- **Purpose**: Handles Web3 connection and transaction management
- **Key Components**:
  - Web3 initialization and account setup
  - Transaction sending with gas estimation
  - Token approval management
  - Formatting utilities
- **Technical Notes**:
  - Uses fallback gas values when estimation fails
  - Implements wait_for_receipt with timeout handling
  - Handles transaction signing and broadcasting

### 3. `contracts.py`
- **Purpose**: Initializes contract instances
- **Key Components**:
  - ABI loading from files
  - Contract initialization with Web3
  - Verification of contract connections
- **Technical Notes**:
  - Handles ABI loading errors gracefully
  - Validates contract connections on startup

### 4. `honey_logic.py`
- **Purpose**: Handles HONEY token operations
- **Key Components**:
  - Balance checking
  - Allowance verification
  - Strategy determination for stirring
- **Technical Notes**:
  - Implements checks for various protocol conditions
  - Manages token allowances for stirring

### 5. `locks_logic.py`
- **Purpose**: Handles LOCKS token operations
- **Key Components**:
  - Floor price and market price retrieval
  - HONEY to LOCKS conversion calculations
  - Swap functionality
- **Technical Notes**:
  - Implements the swap from HONEY to LOCKS
  - Handles price calculation for conversions

### 6. `porridge_logic.py`
- **Purpose**: Handles PORRIDGE operations and protocol actions
- **Key Components**:
  - Borrowing logic
  - PORRIDGE claiming
  - Stirring mechanism
  - Staking functionality
- **Technical Notes**:
  - Implements the core protocol interactions
  - Manages complex stirring calculations and partial stirs

### 7. `notifications.py`
- **Purpose**: Handles Discord notifications
- **Key Components**:
  - Discord webhook integration
  - Message formatting
  - Event collection for batched notifications
- **Technical Notes**:
  - Uses discord-webhook library
  - Implements an event collector for batched messages

### 8. `main.py`
- **Purpose**: Coordinates the protocol interaction cycle
- **Key Components**:
  - Main loop implementation
  - Protocol cycle orchestration
  - Exception handling
- **Technical Notes**:
  - Uses asyncio for async operations
  - Implements try-except blocks for resilience

## Key Workflows

### Borrowing Workflow
1. Check user's borrowing limit via `porridge_contract.functions.userBorrowLimit()`
2. Compare limit to BORROW_THRESHOLD from config
3. If threshold is met, execute borrow transaction
4. Track borrowed amount for subsequent operations
5. **Goldiswap Note**: Borrowing is interest-free with no liquidation risk, which is a key advantage of the protocol

### Claim Workflow
1. Check claimable PORRIDGE via `porridge_contract.functions.userClaimablePrg()`
2. Execute claim transaction if claimable amount > 0
3. Log claimed amount for informational purposes

### Stir Workflow
1. Calculate HONEY needed for full stir based on floor price
2. Determine if full or partial stir is possible based on available HONEY
3. Handle wallet HONEY usage based on ALLOW_WALLET_HONEY setting
4. Approve tokens for stirring
5. Execute stir transaction
6. Track leftover PORRIDGE and used HONEY
7. **Goldiswap Note**: Stirring is a unique mechanism that combines PORRIDGE and HONEY to mint LOCKS at floor price

### Swap Workflow
1. Calculate leftover borrowed HONEY (borrowed_amount - honey_used)
2. Determine swap strategy based on SWAP_ALL_WALLET_HONEY setting
3. Calculate LOCKS amount based on market price (which is determined by the FSL/PSL ratio)
4. Execute buy transaction
5. Track swapped amount
6. **Goldiswap Note**: Buying LOCKS with HONEY happens at market price, which is always above floor price

### Stake Workflow
1. Check unstaked LOCKS balance
2. Approve LOCKS for staking if needed
3. Execute stake transaction
4. **Goldiswap Note**: Staked LOCKS earn PORRIDGE rewards and increase borrowing power

## Smart Contract Interactions

### HONEY Token
- **ERC20 Standard**: implements balanceOf, allowance, approve, transfer
- **Special Functions**: 
  - vaultAdmin() - returns the admin address
  - DOMAIN_SEPARATOR() - for EIP-2612 permit functionality

### LOCKS Token
- **ERC20 Standard**: implements balanceOf, allowance, approve, transfer
- **Price Functions**:
  - floorPrice() - returns the floor price (HONEY per LOCKS)
  - marketPrice() - returns the market price (HONEY per LOCKS)
- **Trading Functions**:
  - buy(uint256 amount, uint256 maxAmount) - buy LOCKS with HONEY at market price
  - tradingActive() - returns if trading is active

### PORRIDGE Contract
- **ERC20 Standard**: implements balanceOf, allowance, approve, transfer
- **Borrow Functions**:
  - userBorrowLimit(address) - returns the user's borrowing limit
  - borrow(uint256) - borrows up to the specified amount
  - userBorrowedHoney(address) - returns borrowed amount
- **Staking Functions**:
  - stake(uint256) - stakes LOCKS tokens
  - userStakedLocks(address) - returns staked LOCKS amount
- **Rewards Functions**:
  - claim() - claims accrued PORRIDGE rewards
  - userClaimablePrg(address) - returns claimable PORRIDGE
- **Stir Function**:
  - stir(uint256) - combines PORRIDGE and HONEY to mint LOCKS at floor price

## Design Decisions

### Modular Architecture
- **Rationale**: Separating concerns improves maintainability and testing
- **Benefit**: Each module has a focused responsibility

### Asynchronous Operations
- **Rationale**: Blockchain transactions require waiting for confirmations
- **Benefit**: Asyncio allows efficient handling of transaction flows

### Separate Token Logic
- **Rationale**: Each token (HONEY, LOCKS, PORRIDGE) has unique operations
- **Benefit**: Cleaner code organization and easier extension

### Event-based Messaging
- **Rationale**: Discord requires minimizing webhook calls to avoid rate limits
- **Benefit**: EventMessageCollector batches messages for a single notification

### Fallback Gas Estimation
- **Rationale**: Some contract functions can't estimate gas properly
- **Benefit**: Fallback values ensure transactions can still proceed

### Goldiswap-Specific Optimizations
- **Rationale**: Understanding Goldiswap's unique mechanisms allows for yield optimization
- **Benefit**: The bot can efficiently cycle through borrow → claim → stir → stake to maximize returns

## Error Handling

The bot implements comprehensive error handling:

1. **Transaction Failures**:
   - Catches and logs transaction reverts
   - Continues to next cycle without crashing

2. **RPC Connection Issues**:
   - Reports connection errors
   - Continues trying in subsequent cycles

3. **Gas Estimation Failures**:
   - Falls back to conservative gas values
   - Logs gas estimation errors

4. **Protocol-Specific Errors**:
   - Handles insufficient funds, balances, and allowances
   - Reports protocol-specific errors to Discord

## Testing Strategy

To test the bot:

1. **Unit Tests**:
   - Test each module in isolation
   - Mock contract interactions
   - not implemented

2. **Read-Only Tests**:
   - Test contract read functions against actual blockchain
   - Verify correct data retrieval

3. **Transaction Tests**:
   - Test in a forked environment or testnet
   - Verify transaction execution and receipt processing
   - not implemented

4. **Integration Tests**:
   - Test full protocol cycle
   - Verify interactions between modules
   - not implemented

## Contributing Guidelines

1. **Fork & Clone**:
   - Fork the repository
   - Clone your fork locally

2. **Create a Branch**:
   - Use descriptive branch names (e.g., `fix-swap-calculation`)

3. **Development Environment**:
   - Set up a virtual environment
   - Install dependencies with `pip install -r requirements.txt`

4. **Testing**:
   - Run tests before submitting changes
   - Add tests for new functionality

5. **Submit a Pull Request**:
   - Include a clear description of changes
   - Reference any related issues

6. **Code Style**:
   - Follow PEP 8 guidelines
   - Use meaningful variable and function names
   - Add docstrings to functions and classes


## References

- [Goldilocks DAO Documentation](https://goldilocks.gitbook.io/docs/)
- [Goldilocks Website](https://www.goldilocksdao.io/goldiswap/)
- [Web3.py Documentation](https://web3py.readthedocs.io/)