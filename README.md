# TradeStation Bot

A Python bot that connects to the TradeStation API to stream and retrieve market data bars for configured symbols.

## Requirements

- Python 3.13+
- [Poetry](https://python-poetry.org/docs/#installation)
- A [TradeStation](https://www.tradestation.com/platforms-and-tools/trading-api/) account with API credentials

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ssammarshall/tradestation_bot
cd tradestation_bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pipx install poetry
poetry install
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your TradeStation API credentials:

```bash
cp .env.example .env
```

```env
CLIENT_ID=YOUR_CLIENT_ID
CLIENT_SECRET=YOUR_CLIENT_SECRET
REFRESH_TOKEN=YOUR_REFRESH_TOKEN
TS_ENV=sim # Use "sim" for simulation or "live" for live trading
ACCOUNT_ID=YOUR_ACCOUNT_ID
SIM_ACCOUNT_ID=YOUR_SIM_ACCOUNT_ID
```

### 5. Configure streams

Edit `stream_config.toml` to define which symbols and bar parameters to stream:

```toml
[[streams]]
symbol = "MNQ"
unit = "Minute"
interval = 1
barsback = 10
session_template = "Default"
```

## Running

### Authenticate

Before running the bot, authenticate with TradeStation to obtain a refresh token:

```bash
python main.py auth
```

### Start the bot

```bash
python main.py run
```
