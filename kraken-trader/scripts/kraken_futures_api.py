#!/usr/bin/env python3
"""
Kraken Futures REST API helper.
Base URL: https://futures.kraken.com/derivatives/api/v3/

Credentials are separate from Kraken Spot — generate futures-specific keys at:
  Kraken Pro → Settings → API → Create API Key (Futures section)

Environment variables:
  KRAKEN_FUTURES_API_KEY
  KRAKEN_FUTURES_API_SECRET

Mutating requests require --confirm-live.

NOTE: Secondary / largely unused in the live workflow. Untested against live
futures (Kraken retired its futures demo ~Jul 2026). Kept for completeness.
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

BASE_URL = "https://futures.kraken.com/derivatives/api/v3"
# .strip() applied to match the spot script and guard against the trailing-newline
# signing bug documented in the handoff (§8, item 1).
API_KEY = os.environ.get("KRAKEN_FUTURES_API_KEY", "").strip()
API_SECRET = os.environ.get("KRAKEN_FUTURES_API_SECRET", "").strip()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _nonce() -> str:
    return str(int(time.time() * 1000))


def _sign(endpoint: str, post_data: str, nonce: str) -> str:
    """
    Authent = Base64(HMAC-SHA256(SHA256(post_data + nonce + endpoint), Base64Decode(secret)))
    endpoint = path only, e.g. /derivatives/api/v3/accounts
    """
    message = (post_data + nonce + endpoint).encode()
    sha256_hash = hashlib.sha256(message).digest()
    mac = hmac.new(base64.b64decode(API_SECRET), sha256_hash, hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(method: str, path: str, params: dict = None, body: dict = None) -> dict:
    url = BASE_URL + path
    post_data = ""
    query_string = ""

    if method == "GET" and params:
        query_string = urllib.parse.urlencode(params)
        url += "?" + query_string

    if method == "POST" and body:
        post_data = urllib.parse.urlencode(body)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if API_KEY and API_SECRET:
        nonce = _nonce()
        endpoint = path  # just the path for signing
        data_to_sign = query_string if method == "GET" else post_data
        sig = _sign(endpoint, data_to_sign, nonce)
        headers["APIKey"] = API_KEY
        headers["Authent"] = sig
        headers["Nonce"] = nonce
    elif path not in ("/tickers", "/instruments"):
        print("ERROR: KRAKEN_FUTURES_API_KEY and KRAKEN_FUTURES_API_SECRET must be set.", file=sys.stderr)
        sys.exit(1)

    data = post_data.encode() if post_data else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _print(data, pretty: bool):
    if pretty:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data))


def _check_errors(result: dict):
    if result.get("error") and result["error"] != "":
        print("ERROR:", result["error"], file=sys.stderr)
        sys.exit(1)
    if result.get("result") == "error":
        print("ERROR:", result.get("error", result), file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_balance(args):
    result = _request("GET", "/accounts")
    _check_errors(result)
    _print(result, args.pretty)


def cmd_positions(args):
    result = _request("GET", "/openpositions")
    _check_errors(result)
    _print(result, args.pretty)


def cmd_open_orders(args):
    result = _request("GET", "/openorders")
    _check_errors(result)
    _print(result, args.pretty)


def cmd_ticker(args):
    if args.symbol:
        result = _request("GET", "/tickers", params={"symbol": args.symbol})
    else:
        result = _request("GET", "/tickers")
    _check_errors(result)
    _print(result, args.pretty)


def cmd_instruments(args):
    result = _request("GET", "/instruments")
    _check_errors(result)
    _print(result, args.pretty)


def cmd_order_history(args):
    params = {}
    if args.symbol:
        params["symbol"] = args.symbol
    result = _request("GET", "/fills", params or None)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_place_order(args):
    if not args.confirm_live:
        print("DRY RUN — add --confirm-live to execute on live account.")
        print(json.dumps({
            "orderType": args.order_type,
            "symbol": args.symbol,
            "side": args.side,
            "size": args.size,
            "limitPrice": args.price,
            "stopPrice": args.stop_price,
            "reduceOnly": args.reduce_only,
            "cliOrdId": args.cl_ord_id,
        }, indent=2))
        return
    body = {
        "orderType": args.order_type,
        "symbol": args.symbol,
        "side": args.side,
        "size": str(args.size),
    }
    if args.price:
        body["limitPrice"] = str(args.price)
    if args.stop_price:
        body["stopPrice"] = str(args.stop_price)
    if args.reduce_only:
        body["reduceOnly"] = "true"
    if args.cl_ord_id:
        body["cliOrdId"] = args.cl_ord_id
    result = _request("POST", "/sendorder", body=body)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_cancel_order(args):
    if not args.confirm_live:
        print("DRY RUN — add --confirm-live to cancel on live account.")
        return
    body = {}
    if args.order_id:
        body["order_id"] = args.order_id
    elif args.cl_ord_id:
        body["cliOrdId"] = args.cl_ord_id
    else:
        print("ERROR: provide --order-id or --cl-ord-id", file=sys.stderr)
        sys.exit(1)
    result = _request("POST", "/cancelorder", body=body)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_cancel_all(args):
    if not args.confirm_live:
        print("DRY RUN — add --confirm-live to cancel ALL open orders on live account.")
        return
    body = {}
    if args.symbol:
        body["symbol"] = args.symbol
    result = _request("POST", "/cancelallorders", body=body)
    _check_errors(result)
    _print(result, args.pretty)


def cmd_list_endpoints(_args):
    endpoints = [
        ("PUBLIC",  "GET",  "/tickers",           "Ticker data for one or all futures"),
        ("PUBLIC",  "GET",  "/instruments",        "All available futures instruments"),
        ("PRIVATE", "GET",  "/accounts",           "Futures account balances"),
        ("PRIVATE", "GET",  "/openpositions",      "Open futures positions"),
        ("PRIVATE", "GET",  "/openorders",         "Open futures orders"),
        ("PRIVATE", "GET",  "/fills",              "Order fill history"),
        ("PRIVATE", "POST", "/sendorder",          "Place a futures order"),
        ("PRIVATE", "POST", "/cancelorder",        "Cancel a futures order"),
        ("PRIVATE", "POST", "/cancelallorders",    "Cancel all open futures orders"),
    ]
    for visibility, method, path, desc in endpoints:
        print(f"{visibility:7s}  {method:4s}  {path:30s}  {desc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_pretty(sp):
    sp.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return sp


def main():
    p = argparse.ArgumentParser(description="Kraken Futures REST API helper")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list-endpoints", help="Show all supported endpoints")

    _add_pretty(sub.add_parser("balance", help="Get futures account balances"))

    _add_pretty(sub.add_parser("positions", help="Get open futures positions"))

    _add_pretty(sub.add_parser("open-orders", help="Get open futures orders"))

    sp = _add_pretty(sub.add_parser("ticker", help="Get futures ticker"))
    sp.add_argument("--symbol", help="e.g. PF_XBTUSD (omit for all)")

    _add_pretty(sub.add_parser("instruments", help="List all available futures instruments"))

    sp = _add_pretty(sub.add_parser("order-history", help="Get fill/order history"))
    sp.add_argument("--symbol", help="Filter by symbol")

    sp = _add_pretty(sub.add_parser("place-order", help="Place a futures order"))
    sp.add_argument("--symbol", required=True, help="e.g. PF_XBTUSD")
    sp.add_argument("--side", required=True, choices=["buy", "sell"])
    sp.add_argument("--order-type", required=True,
                    choices=["lmt", "mkt", "stp", "take_profit", "ioc", "post"],
                    help="Order type: lmt=limit, mkt=market, stp=stop")
    sp.add_argument("--size", required=True, type=float, help="Contract quantity")
    sp.add_argument("--price", type=float, help="Limit price")
    sp.add_argument("--stop-price", type=float, dest="stop_price", help="Stop trigger price")
    sp.add_argument("--reduce-only", action="store_true", dest="reduce_only")
    sp.add_argument("--cl-ord-id", dest="cl_ord_id", help="Client order ID")
    sp.add_argument("--confirm-live", action="store_true",
                    help="Required to execute on live account")

    sp = _add_pretty(sub.add_parser("cancel-order", help="Cancel a futures order"))
    sp.add_argument("--order-id", dest="order_id", help="Order ID to cancel")
    sp.add_argument("--cl-ord-id", dest="cl_ord_id", help="Client order ID to cancel")
    sp.add_argument("--confirm-live", action="store_true")

    sp = _add_pretty(sub.add_parser("cancel-all", help="Cancel all open futures orders"))
    sp.add_argument("--symbol", help="Limit to a specific symbol")
    sp.add_argument("--confirm-live", action="store_true")

    args = p.parse_args()

    dispatch = {
        "list-endpoints": cmd_list_endpoints,
        "balance":        cmd_balance,
        "positions":      cmd_positions,
        "open-orders":    cmd_open_orders,
        "ticker":         cmd_ticker,
        "instruments":    cmd_instruments,
        "order-history":  cmd_order_history,
        "place-order":    cmd_place_order,
        "cancel-order":   cmd_cancel_order,
        "cancel-all":     cmd_cancel_all,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
