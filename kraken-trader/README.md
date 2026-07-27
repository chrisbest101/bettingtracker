# Kraken Trader

Human-in-the-loop, agent-driven trading workflow for Kraken Pro. You paste an analyst
signal (free text), the agent parses it, pulls live market/account data, sizes the position
from a risk %, runs pre-trade guardrail checks, presents a full plan, and **waits for your
explicit confirmation** before placing orders sequentially via a thin signed-REST Python CLI.

```
Analyst signal (free text) → agent parses + sizes + checks → you confirm → kraken_spot_api.py → Kraken REST
```

**The parsing, sizing math, and guardrails live in the agent layer** (`kraken-trading-rules.md`),
not in the Python. The Python is only a signed-REST transport with a dry-run safety default.

## Layout

```
kraken-trader/
├── README.md
├── SKILL.md                     # Skill manifest + fast-path usage
├── kraken-trading-rules.md      # Guardrails / sizing / fee / management rules (the "brain")
├── .env.example                 # Credential template (copy, fill, keep out of git)
├── .gitignore
├── scripts/
│   ├── kraken_spot_api.py       # Spot REST CLI (primary — all live trading)
│   └── kraken_futures_api.py    # Futures REST CLI (secondary, unused/unverified)
└── references/
    ├── auth-and-signing.md      # HMAC signing spec
    └── spot-endpoints.md        # Endpoint + pair reference
```

## Setup

1. Create Kraken API keys (Kraken Pro → Settings → API) with scopes: Query Funds; Query
   Open/Closed Orders & Trades; Create & Modify Orders; Cancel & Close Orders. Enable margin
   trading for leveraged orders.
2. Copy `.env.example` to `~/.kraken_credentials`, fill in values, `chmod 600 ~/.kraken_credentials`.
   No spaces around `=`.
3. Requires **Python 3.7+** only. No third-party dependencies (pure stdlib).

## Usage

```bash
# Read-only
source ~/.kraken_credentials && python3 scripts/kraken_spot_api.py balance --pretty
source ~/.kraken_credentials && python3 scripts/kraken_spot_api.py ticker --symbol XBTUSD --pretty
source ~/.kraken_credentials && python3 scripts/kraken_spot_api.py open-positions --pretty

# Dry run (default — no --confirm-live): prints the order it WOULD send
source ~/.kraken_credentials && python3 scripts/kraken_spot_api.py place-order \
  --symbol XBTUSD --side sell --order-type limit --volume 0.31 --price 66125 --leverage 10

# LIVE order (adds --confirm-live)
source ~/.kraken_credentials && python3 scripts/kraken_spot_api.py place-order \
  --symbol XBTUSD --side sell --order-type limit \
  --volume 0.31 --price 66125 --leverage 10 --timeinforce GTC --confirm-live --pretty
```

## Safety

- **Dry run is the default.** Every mutating command is a no-op unless `--confirm-live` is passed.
- **Place orders sequentially, never in parallel** (parallel → `EAPI:Invalid nonce`).
- **Do not run the live executor in an ephemeral/cloud container.** Keep live keys on a machine
  you control (laptop or always-on server). A throwaway container is fine for read-only/dry-run
  testing only.
- Never commit credentials; never echo keys to the transcript.

## Known gaps / roadmap

See the handoff notes. Highest-value next steps:

1. **Automated fill monitoring** — poll `open-orders`/`open-positions` (or WebSocket) to
   auto-advance the management plan instead of relying on manual "TP1 done" reports.
2. **Persistent trade ledger** — JSON/SQLite keyed by txid: intended plan vs fills vs realized P&L.
3. **Encode sizing/guardrails in code** — especially the TP1 = 50%-of-*filled* rule and the
   1.5% min-TP re-check against the *actual* CMP fill price.
4. **Rate-limit handling / retries** with backoff (currently a hard 10s timeout, no retry).
5. **Secrets hardening** — OS keychain / `keyring` instead of plaintext creds file.
6. **Remote access** — decide between SSH-to-Mac (Tailscale + Termius) vs a hosted runner.
7. **Decide the futures path** — finish or delete (Kraken retired its futures demo ~Jul 2026).
