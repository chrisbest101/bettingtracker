# Kraken Spot — Endpoint Reference

Base URL: `https://api.kraken.com/0`

## Public

| Method | Path | Purpose | Key params |
|---|---|---|---|
| GET | `/public/Ticker` | Live price for sizing/validation | `pair` (optional) |
| GET | `/public/AssetPairs` | Pair name + precision + leverage lookup | `pair` (optional) |
| GET | `/public/OHLC` | Candle data | `pair`, `interval` (mins) |

## Private (require API-Key + API-Sign; nonce in body)

| Method | Path | Purpose | Key params | Permission scope |
|---|---|---|---|---|
| POST | `/private/Balance` | Portfolio equity | — | Query Funds |
| POST | `/private/OpenOrders` | Pending order state | `trades` | Query Open Orders & Trades |
| POST | `/private/OpenPositions` | Open margin positions / fills | `txid` | Query Open Orders & Trades |
| POST | `/private/TradesHistory` | Post-trade P&L breakdown | `start`, `end` | Query Closed Orders & Trades |
| POST | `/private/AddOrder` | Place order | `pair`, `type`, `ordertype`, `volume`, `price`, `leverage`, `timeinforce`, `cl_ord_id` | Create & Modify Orders |
| POST | `/private/CancelOrder` | Cancel one order | `txid` or `cl_ord_id` | Cancel & Close Orders |
| POST | `/private/CancelAll` | Cancel everything | — | Cancel & Close Orders |

## Order types

`market` (CMP entries, some exits), `limit` (entries + take-profits), `stop-loss` (protective
stops). `stop-loss-limit` / `take-profit` / trailing types supported but not routinely used.

## Pair map

| Common | Kraken |
|---|---|
| BTC/USD | `XBTUSD` |
| ETH/USD | `ETHUSD` |
| SOL/USD | `SOLUSD` |
| BTC/EUR | `XBTEUR` |
| ETH/BTC | `ETHXBT` |

Always verify a pair via `/public/AssetPairs` before trading.

## Required API-key permission scopes

Query Funds; Query Open Orders & Trades; Query Closed Orders & Trades; Create & Modify Orders;
Cancel & Close Orders. Enable margin trading on the account for leveraged orders.
