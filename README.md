# Bitcoin-ethereum-bot
Asynchronous trading bot for Binance in Python. It uses real-time WebSockets, mathematical precision with Decimal, and automatic state management to execute a dip-buying and take-profit strategy.
# Binance Async All-In Trading Bot 🤖📈

A high-performance automated trading bot developed in **Python**, designed to trade asynchronously on **Binance**. The script uses WebSockets to monitor prices in real time without unnecessary latency and applies rigorous numerical precision handling with the `Decimal` library to avoid financial rounding errors.

---

## 🚀 Main Features

* **100% Asynchronous (`asyncio`):** Capable of monitoring multiple cryptocurrency pairs simultaneously in a non-blocking manner.

* **Real-Time WebSockets:**

* Connection to `aggTrade` for dynamic tracking of price spikes and dips.

* Connection to `user_socket` (User Data Stream) to instantly listen when your sell orders are executed on Binance.

* * **Financial Accuracy (Decimal):** Avoids common errors associated with traditional floating-point numbers when calculating quantities, entry prices, and sell targets.

* **Binance Dynamic Filters:** Automatically queries API filters (`LOT_SIZE` and `PRICE_FILTER`) to adjust the decimal places and steps allowed by the exchange (`stepSize` and `tickSize`).

* **State Persistence:** Saves active positions in a `positions.json` file. If the bot restarts or the connection is lost, it doesn't lose track of its open trades.

* **Error and Log Management:** Detailed activity logging in the console and in a `bot_log.txt` file.

---

## 📊 How Does the Strategy Work?


1. **Scanning:** The bot listens to the prices of the configured pairs (e.g., `BTCUSDT`, `ETHUSDT`, `PAXGUSDT`, etc.).

2. **Drop Detection (`DROP_BUY`):** If the price drops by a certain percentage from its recent high (set to `0.1%` by default), the bot calculates the available free balance in the bridge currency (`USDT` or `BTC`) and executes a **Buy at Market (Dynamic All-In)** order.

3. **Take Profit (`TAKE_PROFIT`):** Immediately after buying, it calculates the target price with the expected profit (`0.2%` by default) and places a **Limit Sell** order.

4. **Monitoring:** The bot waits via WebSockets for the sell order to complete before releasing the capital and restarting the cycle.

---

## 🛠️ Prerequisites

* Python 3.8 or higher installed.

* A Binance account with enabled API keys (with Spot Trading permissions).

---

## ⚙️ Installation and Configuration

1. **Clone this repository:**
```bash

git clone [https://github.com/your-username/your-repository.git](https://github.com/your-username/your-repository.git)

cd your-repository
