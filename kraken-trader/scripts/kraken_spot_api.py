#!/usr/bin/env python3
"""
Kraken Spot REST API helper.
Credentials loaded from environment variables only.
Mutating requests require --confirm-live.
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("KRAKEN_API_BASE", "https://api.kraken.com")
API_VERSION = "/0"
API_KEY = os.environ.get("KRAKEN_API_KEY", "").strip()
API_SECRET = os.environ.get("KRAKEN_API_SECRET", "").strip()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _sign(urlpath: str, data: dict) -> str:
    """HMAC-SHA512 of (urlpath + SHA256(nonce + urlencode(data))) using base64-decoded secret."""
    encoded = (str(data["nonce"]) + urllib.parse.urlencode(data)).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(API_SECRET), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


def _nonce() -> str:
    return str(time.time_ns())


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _public_get(path: str, params: dict = None) -> dict:
    url = BASE_URL + API_VERSION + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _private_post(path: str, data: dict) -> dict:
    if not API_KEY or not API_SECRET:
        print("ERROR: KRAKEN_API_KEY and KRAKEN_API_SECRET must be set.", file=sys.stderr)
        sys.exit(1)
    data["nonce"] = _nonce()
    urlpath = API_VERSION + path
    sig = _sign(urlpath, data)
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        BASE_URL + urlpath,
        data=payload,
        headers={
            "API-Key": API_KEY,
            "API-Sign": sig,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _print(data, pretty: bool):
    if pretty:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data))


def _check_errors(result: dict):
    if result.get("error"):
        print("ERROR:", result["error"], file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_ticker(args):
    params = {}
    if args.symbol:
        params["pair"] = args.symbol
    result = _public_get("/public/Ticker", params or None)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_asset_pairs(args):
    params = {}
    if args.symbol:
        params["pair"] = args.symbol
    result = _public_get("/public/AssetPairs", params or None)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_ohlc(args):
    params = {"pair": args.symbol}
    if args.interval:
        params["interval"] = args.interval
    result = _public_get("/public/OHLC", params)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_balance(args):
    result = _private_post("/private/Balance", {})
    _check_errors(result)
    _print(result, args.pretty)


def cmd_open_orders(args):
    data = {}
    if args.trades:
        data["trades"] = "true"
    result = _private_post("/private/OpenOrders", data)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_open_positions(args):
    data = {}
    if args.txid:
        data["txid"] = args.txid
    result = _private_post("/private/OpenPositions", data)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_trade_history(args):
    data = {}
    if args.start:
        data["start"] = args.start
    if args.end:
        data["end"] = args.end
    result = _private_post("/private/TradesHistory", data)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_place_order(args):
    if not args.confirm_live:
        print("DRY RUN — add --confirm-live to execute on live account.")
        print(json.dumps({
            "pair": args.symbol,
            "type": args.side,
            "ordertype": args.order_type,
            "price": args.price,
            "volume": args.volume,
            "leverage": args.leverage,
            "timeinforce": args.timeinforce,
            "cl_ord_id": args.cl_ord_id,
        }, indent=2))
        return
    data = {
        "pair": args.symbol,
        "type": args.side,
        "ordertype": args.order_type,
        "volume": str(args.volume),
    }
    if args.price:
        data["price"] = str(args.price)
    if args.leverage:
        data["leverage"] = str(args.leverage)
    if args.timeinforce:
        data["timeinforce"] = args.timeinforce
    if args.cl_ord_id:
        data["cl_ord_id"] = args.cl_ord_id
    result = _private_post("/private/AddOrder", data)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_cancel_order(args):
    if not args.confirm_live:
        print("DRY RUN — add --confirm-live to cancel on live account.")
        return
    data = {}
    if args.txid:
        data["txid"] = args.txid
    elif args.cl_ord_id:
        data["cl_ord_id"] = args.cl_ord_id
    else:
        print("ERROR: provide --txid or --cl-ord-id", file=sys.stderr)
        sys.exit(1)
    result = _private_post("/private/CancelOrder", data)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_cancel_all(args):
    if not args.confirm_live:
        print("DRY RUN — add --confirm-live to cancel ALL open orders on live account.")
        return
    result = _private_post("/private/CancelAll", {})
    _check_errors(result)
    _print(result, args.pretty)


def cmd_list_endpoints(_args):
    endpoints = [
        ("PUBLIC",  "GET",  "/public/Ticker",        "Ticker info for one or all pairs"),
        ("PUBLIC",  "GET",  "/public/AssetPairs",     "Tradable asset pair details"),
        ("PUBLIC",  "GET",  "/public/OHLC",           "OHLC candle data"),
        ("PRIVATE", "POST", "/private/Balance",       "Account cash balances"),
        ("PRIVATE", "POST", "/private/OpenOrders",    "Currently open orders"),
        ("PRIVATE", "POST", "/private/OpenPositions", "Open margin positions"),
        ("PRIVATE", "POST", "/private/TradesHistory", "Trade history"),
        ("PRIVATE", "POST", "/private/AddOrder",      "Place a new order"),
        ("PRIVATE", "POST", "/private/CancelOrder",   "Cancel a single order"),
        ("PRIVATE", "POST", "/private/CancelAll",     "Cancel all open orders"),
    ]
    for visibility, method, path, desc in endpoints:
        print(f"{visibility:7s}  {method:4s}  {path:35s}  {desc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_pretty(sp):
    sp.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return sp


def main():
    p = argparse.ArgumentParser(description="Kraken Spot REST API helper")
    sub = p.add_subparsers(dest="command", required=True)

    # list-endpoints
    sub.add_parser("list-endpoints", help="Show all supported endpoints")

    # ticker
    sp = _add_pretty(sub.add_parser("ticker", help="Get spot ticker"))
    sp.add_argument("--symbol", help="Trading pair e.g. XBTUSD (omit for all)")

    # asset-pairs
    sp = _add_pretty(sub.add_parser("asset-pairs", help="Get tradable asset pairs"))
    sp.add_argument("--symbol", help="Filter to specific pair")

    # ohlc
    sp = _add_pretty(sub.add_parser("ohlc", help="Get OHLC candle data"))
    sp.add_argument("--symbol", required=True, help="Trading pair e.g. XBTUSD")
    sp.add_argument("--interval", type=int, default=60, help="Candle interval in minutes (default 60)")

    # balance
    _add_pretty(sub.add_parser("balance", help="Get account balances"))

    # open-orders
    sp = _add_pretty(sub.add_parser("open-orders", help="Get open orders"))
    sp.add_argument("--trades", action="store_true", help="Include trade data")

    # open-positions
    sp = _add_pretty(sub.add_parser("open-positions", help="Get open margin positions"))
    sp.add_argument("--txid", help="Filter by transaction ID")

    # trade-history
    sp = _add_pretty(sub.add_parser("trade-history", help="Get trade history"))
    sp.add_argument("--start", help="Start timestamp (Unix)")
    sp.add_argument("--end", help="End timestamp (Unix)")

    # place-order
    sp = _add_pretty(sub.add_parser("place-order", help="Place a new order"))
    sp.add_argument("--symbol", required=True, help="Trading pair e.g. XBTUSD")
    sp.add_argument("--side", required=True, choices=["buy", "sell"])
    sp.add_argument("--order-type", required=True,
                    choices=["market", "limit", "stop-loss", "take-profit",
                             "stop-loss-limit", "take-profit-limit", "trailing-stop",
                             "trailing-stop-limit", "settle-position"],
                    help="Order type")
    sp.add_argument("--volume", required=True, type=float, help="Order quantity")
    sp.add_argument("--price", type=float, help="Limit price (required for limit orders)")
    sp.add_argument("--leverage", help="Leverage for margin e.g. 2, 3, 4, 5")
    sp.add_argument("--timeinforce", choices=["GTC", "IOC", "GTD"], default="GTC")
    sp.add_argument("--cl-ord-id", dest="cl_ord_id", help="Client order ID")
    sp.add_argument("--confirm-live", action="store_true",
                    help="Required to execute on live account")

    # cancel-order
    sp = _add_pretty(sub.add_parser("cancel-order", help="Cancel an order"))
    sp.add_argument("--txid", help="Transaction ID to cancel")
    sp.add_argument("--cl-ord-id", dest="cl_ord_id", help="Client order ID to cancel")
    sp.add_argument("--confirm-live", action="store_true",
                    help="Required to execute on live account")

    # cancel-all
    sp = _add_pretty(sub.add_parser("cancel-all", help="Cancel all open orders"))
    sp.add_argument("--confirm-live", action="store_true",
                    help="Required to execute on live account")

    args = p.parse_args()

    dispatch = {
        "list-endpoints":  cmd_list_endpoints,
        "ticker":          cmd_ticker,
        "asset-pairs":     cmd_asset_pairs,
        "ohlc":            cmd_ohlc,
        "balance":         cmd_balance,
        "open-orders":     cmd_open_orders,
        "open-positions":  cmd_open_positions,
        "trade-history":   cmd_trade_history,
        "place-order":     cmd_place_order,
        "cancel-order":    cmd_cancel_order,
        "cancel-all":      cmd_cancel_all,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
