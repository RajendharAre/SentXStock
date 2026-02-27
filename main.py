"""
Sentiment Trading Agent — Main CLI Entry Point.
Run this to execute the full trading agent pipeline.

Usage:
    python main.py                    # Real-time mode (needs API keys)
    python main.py --mock             # Mock data only (no API keys needed)
    python main.py --tickers AAPL MSFT TSLA
"""

import sys
import json
import argparse
from agent.agent import TradingAgent


def main():
    parser = argparse.ArgumentParser(
        description="Sentiment Trading Agent — Autonomous portfolio management"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data only (no API keys needed)",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=None,
        help="Tickers to monitor (e.g., AAPL MSFT TSLA)",
    )
    parser.add_argument(
        "--risk",
        choices=["Low", "Medium", "High"],
        default="Medium",
        help="Starting risk level (default: Medium)",
    )
    parser.add_argument(
        "--cash",
        type=float,
        default=50000.0,
        help="Starting cash amount (default: 50000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save output JSON to file (e.g., output.json)",
    )

    args = parser.parse_args()

    # Build custom portfolio if args provided
    portfolio = None
    if args.risk != "Medium" or args.cash != 50000.0:
        from portfolio.portfolio import DEFAULT_PORTFOLIO
        portfolio = DEFAULT_PORTFOLIO.copy()
        portfolio["holdings"] = {
            k: v.copy() for k, v in DEFAULT_PORTFOLIO["holdings"].items()
        }
        portfolio["risk_level"] = args.risk
        portfolio["cash"] = args.cash

    # Initialize agent
    use_realtime = not args.mock
    agent = TradingAgent(portfolio=portfolio, use_realtime=use_realtime)

    # Run the agent
    result = agent.run(tickers=args.tickers)

    # Print JSON output
    output_json = json.dumps(result, indent=2)
    print("\n📊 AGENT OUTPUT (JSON):")
    print("-" * 40)
    print(output_json)

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
        print(f"\n💾 Output saved to {args.output}")

    return result


if __name__ == "__main__":
    main()
