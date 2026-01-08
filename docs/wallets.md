# Wallets API

Base path: `/api/v1/`

## List wallets

- Method: `GET`
- Path: `/api/v1/wallets/`
- Auth: `Bearer <access>`

Response:
- `200 OK` list of wallets

Sample response (JSON):

```json
[
  {
    "id": 1,
    "name": "Primary",
    "wallet_type": "current",
    "balance": "1500.00",
    "status": "active",
    "created_at": "2026-01-07T10:30:00Z",
    "updated_at": "2026-01-07T10:30:00Z"
  }
]
```

## Retrieve wallet

- Method: `GET`
- Path: `/api/v1/wallets/{id}/`
- Auth: `Bearer <access>`

Response:
- `200 OK` wallet details

Sample response (JSON):

```json
{
  "id": 1,
  "name": "Primary",
  "wallet_type": "current",
  "balance": "1500.00",
  "status": "active",
  "created_at": "2026-01-07T10:30:00Z",
  "updated_at": "2026-01-07T10:30:00Z"
}
```

## Create wallet

- Method: `POST`
- Path: `/api/v1/wallets/`
- Auth: `Bearer <access>`

Request body (JSON):

```json
{
  "name": "Primary",
  "wallet_type": "current"
}
```

Response:
- `201 Created` wallet details

## Notes

- `wallet_type` choices: `current`, `savings`, `travel`, `business`, `other`.
- Wallet names are unique per user (case-insensitive validation at API layer).
- Access is restricted to the wallet owner.
