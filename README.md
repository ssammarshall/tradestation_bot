# TradeStation Bot

A Python bot that connects to the TradeStation API to stream and retrieve market data bars, run configured strategy assignments, and place orders.

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

| Variable | Required | Description |
| --- | --- | --- |
| `CLIENT_ID` | yes | TradeStation API client ID. |
| `CLIENT_SECRET` | yes | TradeStation API client secret. |
| `REFRESH_TOKEN` | yes | Obtained via `python main.py auth` (see below). |
| `TS_ENV` | yes | `sim` (paper) or `live`. Selects API host and active account. |
| `ACCOUNT_ID` | when `TS_ENV=live` | Live account ID. |
| `SIM_ACCOUNT_ID` | when `TS_ENV=sim` | Simulation account ID. |
| `REDIRECT_URI` | no | OAuth redirect URI. Defaults to `http://localhost:3000`. Must match the redirect URI registered for your TradeStation API app. |

### 5. Configure streams

`stream_config.toml` defines the symbols and bar parameters used by the standalone stream script (`scripts/run_stream.py`). It is independent from strategy assignments.

```toml
[[streams]]
symbol = "MNQ"
unit = "Minute"
interval = 1
barsback = 10
session_template = "Default"
```

### 6. Configure strategy assignments

`strategy_assignments.toml` defines which strategies the bot runs when invoked with `python main.py run`. Each `[[assignments]]` block binds a setup and entry to a symbol, bar stream, and trade window.

```toml
[[assignments]]
name = "ict_liquidity_sweep_ny_session_strategy"
symbol = "MNQ"
unit = "Minute"
interval = 1
session_template = "USEQ24Hour"
setup = "ny_ifvg_liquidity_sweep"
entry = "retracement"
trade_window_start = "13:30"
trade_window_end = "15:30"
max_num_of_trades = 2
```

| Field | Description |
| --- | --- |
| `name` | Unique identifier for the assignment. Also used as the logger name (see `logging.toml` overrides). |
| `symbol` | Instrument symbol (e.g. `MNQ`). |
| `unit` / `interval` | Bar size — e.g. `Minute` + `1` for 1-minute bars. |
| `session_template` | TradeStation session template (e.g. `Default`, `USEQ24Hour`). |
| `setup` | Setup name registered in [app/strategies/registry.py](app/strategies/registry.py). |
| `entry` | Entry name registered in [app/strategies/registry.py](app/strategies/registry.py). |
| `trade_window_start` / `trade_window_end` | `HH:MM` (UTC). The strategy subscribes to its stream only inside this window. |
| `max_num_of_trades` | Trade cap per window. The strategy unsubscribes once reached. |

Available setups and entries are registered in [app/strategies/registry.py](app/strategies/registry.py):

- Setups: `ny_ifvg_liquidity_sweep`
- Entries: `retracement`

To add new ones, implement the appropriate base class under [app/strategies/setups/](app/strategies/setups/) or [app/strategies/entries/](app/strategies/entries/) and register it in [build_default_registry](app/strategies/registry.py#L23).

### 7. Configure logging

`logging.toml` controls log verbosity. The top-level `level` is the root level; `[overrides]` sets per-logger levels by name. Strategy assignments log under their `name`, and components like `StreamManager` use their class name.

```toml
level = "INFO"

[overrides]
"ict_liquidity_sweep_ny_session_strategy" = "DEBUG"
"StreamManager" = "DEBUG"
```

## Running

The CLI is `python main.py <command>`.

### Authenticate

Before running the bot for the first time, authenticate with TradeStation to obtain a refresh token. Paste the returned `REFRESH_TOKEN` into your `.env`.

```bash
python main.py auth
```

### View account info

Prints all accounts, the active account based on `TS_ENV`, and current balances.

```bash
python main.py account
```

### Start the bot

Loads `strategy_assignments.toml`, subscribes each strategy to its stream during its trade window, and evaluates closed bars against the configured setup and entry.

```bash
python main.py run
```

Stop with `Ctrl+C` — the bot will unsubscribe streams and close the HTTP client cleanly.

## Useful scripts

In addition to the CLI commands, [scripts/](scripts/) contains standalone utilities:

- [scripts/run_stream.py](scripts/run_stream.py) — stream bars defined in `stream_config.toml` and print them.
- [scripts/run_order.py](scripts/run_order.py) — place sample market and bracket orders (edit `SYMBOL` / `QUANTITY` first).
- [scripts/close_all_positions.py](scripts/close_all_positions.py) — close every open position on the active account.

Run any of these directly with `python scripts/<name>.py`.
