# Kraken Spot — Auth & Signing

- **Headers:** `API-Key` (public key), `API-Sign` (HMAC-SHA512 signature). Include `nonce`
  in the POST body.
- **Signature:**
  `API-Sign = Base64(HMAC-SHA512(urlpath + SHA256(nonce + urlencode(POST_data)), Base64Decode(API_secret)))`
- **Steps:**
  1. `nonce = str(time.time_ns())`
  2. urlencode the POST body (with nonce included)
  3. `SHA256(nonce + body)`
  4. prepend the urlpath bytes
  5. HMAC-SHA512 with the base64-decoded secret
  6. base64-encode the result
- **URI path for signing** must start with `/0/private`.
- **Nonce** must be strictly increasing (nanoseconds avoid collisions on parallel requests —
  but still place mutating orders sequentially).
- If **2FA** is enabled on the key, include `otp` in the body.

## Futures signing (separate scheme)

- **Headers:** `APIKey`, `Authent`, `Nonce`.
- `Authent = Base64(HMAC-SHA256(SHA256(post_data + nonce + endpoint), Base64Decode(secret)))`
  where `endpoint` is the path only.

## Credential hygiene

- Store keys in `~/.kraken_credentials` (`chmod 600`, gitignored). Format — **no spaces
  around `=`** or the shell exports an empty value:

  ```bash
  export KRAKEN_API_KEY=<KRAKEN_API_KEY>
  export KRAKEN_API_SECRET=<KRAKEN_API_SECRET>
  ```

- Code `.strip()`s key and secret to remove trailing newlines (a real bug that broke signing).
- Never echo keys to the transcript.
