---
name: kraken-trader-skill
description: Use when the user wants Kraken Pro API automation via REST for spot or futures trading, including order execution from natural language, cancel/query, and market/account data retrieval.
metadata:
  version: "1.1.0"
---

# Kraken Trader Skill

Use `scripts/kraken_spot_api.py` for spot trading.
Use `scripts/kraken_futures_api.py` for futures/derivatives trading.

For private endpoints, set credentials (never commit these values):

    # Spot
    export KRAKEN_API_KEY="<KRAKEN_API_KEY>"
    export KRAKEN_API_SECRET="<KRAKEN_API_SECRET>"
    # Futures (separate keys)
    export KRAKEN_FUTURES_API_KEY="<REDACTED>"
    export KRAKEN_FUTURES_API_SECRET="<REDACTED>"

The recommended pattern is a `~/.kraken_credentials` file (chmod 600, gitignored)
sourced before each call:

    source ~/.kraken_credentials && python3 scripts/kraken_spot_api.py balance --pretty

## Safety Policy
- Never send mutating requests without `--confirm-live`. Absence of the flag = dry run.
- Default flow is direct live execution (no sandbox). There is no testnet.
- Place orders **sequentially**, never in parallel (parallel calls collide on the
  nonce → `EAPI:Invalid nonce`).
- If instruction is ambiguous or missing fields, ask only for the missing fields.
- Kraken pair names differ from common names: BTC → XBT. Verify via `/public/AssetPairs`.

## Guardrails, sizing and fee rules
The full pre-trade guardrails, position-sizing formula, fee model, and trade-management
rules live in `kraken-trading-rules.md` in this folder. Load that file before parsing a
signal or sizing a trade — it is the reasoning "brain" of the workflow.

## Reference
- `references/auth-and-signing.md` — HMAC-SHA512 signing spec (spot).
- `references/spot-endpoints.md` — endpoint parameter reference + pair map.
