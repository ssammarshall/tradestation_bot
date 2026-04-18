from config.settings import Settings
from app.broker.tradestation_client import TradeStationClient
from app.account.account_service import AccountService

settings = Settings()
client = TradeStationClient(settings)
account_service = AccountService(client)

# ---------------------------------------------------------------------------
# All accounts
# ---------------------------------------------------------------------------

accounts_response = account_service.get_accounts()
print("=== Accounts ===")
for account in accounts_response.accounts:
    print(f"  id={account.account_id} type={account.account_type} alias={account.alias} status={account.status}")

# ---------------------------------------------------------------------------
# Active account (live or sim based on TS_ENV)
# ---------------------------------------------------------------------------

account_id = settings.active_account_id
print(f"\n=== Active Account ({settings.environment}) ===")
print(f"  account_id={account_id}")

# ---------------------------------------------------------------------------
# Balance for active account
# ---------------------------------------------------------------------------

balance_response = account_service.get_balance(account_id)
print("\n=== Balance ===")
for balance in balance_response.balances:
    print(f"  cash_balance={balance.cash_balance}")
    print(f"  buying_power={balance.buying_power}")
    print(f"  equity={balance.equity}")
    print(f"  market_value={balance.market_value}")
    print(f"  todays_profit_loss={balance.todays_profit_loss}")
    print(f"  unrealized_profit_loss={balance.unrealized_profit_loss}")
