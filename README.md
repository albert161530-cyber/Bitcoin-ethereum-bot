# Bitcoin-Ethereum-Bot

Asynchronous trading bot for Binance written in Python. It uses real-time WebSockets, precise financial calculations with `Decimal`, and automatic state management to execute a dip-buying and take-profit strategy.

# Binance Async All-In Trading Bot 🤖📈

An asynchronous automated trading bot built with **Python** for **Binance Spot trading**. It uses real-time WebSockets to monitor cryptocurrency prices, tracks price peaks and dips, and applies precise numerical calculations with Python's `Decimal` library to avoid floating-point rounding errors.

## 🚀 Key Features

- **Fully Asynchronous (`asyncio`):** Monitors multiple cryptocurrency pairs simultaneously without blocking execution.
- **Real-Time WebSockets:**
  - Connects to `aggTrade` streams to track price movements, peaks, and dips.
  - Connects to the Binance User Data Stream to detect when sell orders are executed.
- **Financial Precision (`Decimal`):** Avoids common floating-point errors when calculating order quantities, entry prices, and take-profit targets.
- **Dynamic Binance Filters:** Retrieves exchange filters such as `LOT_SIZE` and `PRICE_FILTER` to comply with the required `stepSize` and `tickSize`.
- **State Persistence:** Stores active positions in `positions.json` to preserve trading state across restarts.
- **Error Handling and Logging:** Records bot activity, trading events, and errors in the console and `bot_log.txt`.

## 📊 How the Strategy Works

1. **Price Tracking:** Monitors configured cryptocurrency pairs, such as `BTCUSDT`, `ETHUSDT`, and `PAXGUSDT`.
2. **Dip Detection (`DROP_BUY`):** When the price drops by a configured percentage from its recent peak (default: `0.1%`), the bot calculates the available free balance in the quote asset, such as `USDT` or `BTC`, and submits a **market buy order** using the available balance.
3. **Take Profit (`TAKE_PROFIT`):** After buying, the bot calculates a target sell price based on the configured profit percentage (default: `0.2%`) and places a **limit sell order**.
4. **Order Monitoring:** Listens for order execution updates through WebSockets. Once the sell order is completed, the bot releases the capital for the next trading cycle.

## 🛠️ Prerequisites

- Python 3.8 or higher.
- A Binance account.
- Binance API credentials with **Spot Trading** permissions.
- The required Python dependencies listed in `requirements.txt`.

## ⚙️ Installation and Configuration

### Step 1: Clone the repository

```
git clone https://github.com/your-username/your-repository.git
cd your-repository
```

Replace `your-username/your-repository` with the actual GitHub repository URL.

### Step 2: Install dependencies

Install the required packages using:

```
pip install -r requirements.txt
```

### Step 3: Configure API credentials

The bot reads API credentials directly from operating-system environment variables using `os.getenv()`. It does not load a local `.env` file or require API keys to be hardcoded in the source code.

Set the variables in the same terminal session used to run the bot.

**Linux / macOS (Bash):**

```
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

**Windows (PowerShell):**

```
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

**Windows (Command Prompt):**

```
set BINANCE_API_KEY=your_api_key_here
set BINANCE_API_SECRET=your_api_secret_here
```

**Security:** Use API keys with only the permissions required by the bot. Do not enable withdrawals, and never commit credentials to GitHub.

## ▶️ Execution

After configuring the environment variables, start the bot with:

```
python bot.py
```

## 📁 File Structure

```
your-repository/
├── bot.py
├── requirements.txt
├── positions.json
└── bot_log.txt
```

- **`bot.py`** — Main script containing the trading logic, WebSocket connections, and order management.
- **`requirements.txt`** — List of Python dependencies.
- **`positions.json`** — Automatically generated file used to persist active positions.
- **`bot_log.txt`** — Log file containing trading events, operational messages, and errors.

The `positions.json` and `bot_log.txt` files should be excluded from version control if they contain sensitive information or local runtime data.

## ⚠️ Risk Notice

This bot places real orders when connected to a live Binance account. Market orders can execute at prices different from the latest observed price, and trading fees, slippage, minimum order requirements, and exchange restrictions affect profitability. Test the strategy using Binance Spot Testnet before trading with real funds.

Add a clear project-purpose introductionResolve the duplicated project headings
