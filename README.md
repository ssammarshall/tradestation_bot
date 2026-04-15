# TradeStation Bot

A Python bot that connects to the TradeStation API to stream and retrieve market data bars for configured symbols.

## Requirements

- Python 3.13+
- [Poetry](https://python-poetry.org/docs/#installation)
- A TradeStation account with API credentials

## Setup

### 1. Clone the repository

```bash
git clone <https://github.com/ssammarshall/tradestation_bot>
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
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REFRESH_TOKEN=your_refresh_token
ACCOUNT_ID=your_account_id
TS_ENV=sim  # Use "sim" for simulation or "live" for live trading
```

### 5. Configure streams

Edit `stream_config.toml` to define which symbols and bar parameters to stream:

```toml
[[streams]]
symbol = "@MNQ"
unit = "Minute"
interval = 1
barsback = 10
session_template = "Default"
```

## Running

```bash
python main.py
```
