# Kraken Trading Rules (agent memory / "brain")

These are the guardrails, sizing math, fee model, and trade-management rules the agent
applies conversationally. The Python CLI is only a signed-REST transport — **all parsing,
sizing, and checks live here.**

---

## Signal parsing

| Signal token | Parsed field | Transform |
|---|---|---|
| `Ticker: BTC-USD` | `pair` | Map to Kraken name: BTC→**XBT** (`XBTUSD`), `ETHUSD`, `SOLUSD`. Verify via `/public/AssetPairs`. |
| `Direction: Long/Short` | `side` | Long → entries `buy`, exits `sell`. Short → entries `sell`, exits `buy`. |
| `Entries: [prices]` | `price` + `ordertype` | `CMP` → `market`; numeric level → `limit`. Multiple = multiple orders. |
| `Take Profits: [prices]` | reduce-side `limit` orders | Cap at 2 exits (see guardrail 7). |
| `Stoploss: X` | `stop-loss` order (reduce side) | If "hard SL" + "candle close" both given, use the **hard** SL as the order. |
| `Risk Level` | risk % | `Moderate` → 2% of portfolio; `Risky` → 1% (recommend). |
| `Leverage: 5x–50x` | `leverage` | **Ignore the signal's number.** Use Kraken's per-pair max (or lower). |
| user-stated risk % | sizing input | Overrides the Risk Level default. |

**Size is never taken from the signal — always computed from risk %.**

---

## Guardrail checks (run in order, before any order is sent)

1. **Account/margin clear** — query `balance`, `open-positions`, `open-orders`. Confirm free
   margin; no conflicting orders reserving it. Fail → warn, ask to cancel leftovers
   (common cause of `EOrder:Insufficient initial margin`).
2. **Tradable on Kraken** — reject commodities/FX (e.g. XAU/USD gold). Fail → block.
3. **Pair-name normalization** — BTC→XBT etc., verify via `/public/AssetPairs`. Unknown → block, ask.
4. **Max-leverage clamp** — use Kraken's cap, never the signal's. Known maxes: BTC/USD 10x,
   SOL/USD 10x, ETH/USD 5x, BTC/GBP 5x, LINK/GBP spot-only. Fail → warn + clamp.
5. **Minimum TP-distance (fee) check** — each TP ≥ **1.5%** price move from entry (≈2× the
   ~0.75% taker round-trip). Fail → warn, recommend dropping that leg.
6. **Stop-distance sanity** — SL ≥ **0.5%** from entry. Fail → warn, suggest widening.
7. **Max exit legs** — **≤2 exits** (TP1 + one more). 3 TPs → prompt which two to use.
8. **SL-already-breached** — if session high/low already pierced SL, flag it. Fail → warn.
9. **Position sizing by risk %** — see formula below.
10. **TP1 partial-exit sizing** — TP1 volume = **50% of FILLED entries only**, not 50% of
    total planned. If only Entry 1 filled, TP1 = 50% of Entry 1; top up when Entry 2 fills.
11. **Margin-stacking** — place **SL + TP1 first**, add **TP2 after TP1 fills** (avoids
    `EOrder:Insufficient initial margin`).
12. **Confirmation (mandatory)** — present full plan (orders, sizes, net P&L after fees,
    £ at risk, R/R) and wait for explicit "yes". CLI also requires `--confirm-live`.

---

## Position-sizing formula

```
risk_GBP        = portfolio_equity_GBP × risk_pct
risk_USD        = risk_GBP × GBP/USD_rate
sl_distance_USD = | avg_entry_price − stop_price |
position_size   = risk_USD ÷ sl_distance_USD          # base units, e.g. BTC
per_entry_size  = position_size ÷ number_of_entries
margin_locked   = (position_size × entry_price) ÷ leverage
```

---

## Fee model (for projections)

- **Taker (market):** ~0.375% of notional per side.
- **Maker (limit):** ~0.10% of notional per side.
- **Break-even move:** ~0.75% (taker both sides) / ~0.20% (maker both sides).
- **Rollover (margin overnight):** ~0.025% per 4h (BTC seen at 0.042%/4h).
- Guardrail 5 (1.5% min TP) exists to clear these with margin to spare.
- Prefer **limit (maker)** entries.

---

## Trade management

- Standard place sequence per trade: Entry 1 → Entry 2 → Stop-loss (full size) →
  TP1 (50% of filled). TP2 added **after** TP1 fills.
- After TP1 fills: cancel SL, move SL to **breakeven** (entry), place TP2.
- Orders **sequential**, never parallel (nonce collisions).
- Trade USD pairs (`XBTUSD`/`ETHUSD`/`SOLUSD`) and keep profits in USD to avoid GBP basis risk.
- Fill notification is **manual**: the user reports "TP1 done" and the agent re-queries state
  (`open-orders`, `open-positions`, `trade-history`) and advances the plan. No watcher process.

---

## Kraken-specific notes

- 10x-or-spot-only depending on pair; always pass `--leverage` explicitly (incl. on stops)
  so the order description shows the intended ratio.
- Pair map: BTC/USD→`XBTUSD`, ETH/USD→`ETHUSD`, SOL/USD→`SOLUSD`, BTC/EUR→`XBTEUR`, ETH/BTC→`ETHXBT`.
- `CMP` = current market price = enter **now at market**, not a resting limit. Re-check TP
  distances against the **actual fill price**, not the stale CMP in the signal.
