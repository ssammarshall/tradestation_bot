import argparse
import runpy

commands = ["account", "auth", "run"]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TradeStation Bot CLI")
    parser.add_argument(
        "command",
        choices=commands,
        help="Command to execute: auth or run",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "account":
        print("Fetching account info...\n")
        runpy.run_path("scripts/run_account.py")
    elif args.command == "auth":
        print("Authenticating with TradeStation...\n")
        runpy.run_path("scripts/run_auth.py")
    elif args.command == "run":
        print("Running the bot...\n")
        runpy.run_path("scripts/run_assignments.py")