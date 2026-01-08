# Transactions API

Base path: `/api/v1/`

## Deposit

- Method: `POST`
- Path: `/api/v1/wallets/{reference_tag}/deposit/`
- Auth: `Bearer <access>`

Request body (JSON):

```json
{
  "amount": "10.00",
  "external_source": "bank",
  "metadata": {"note": "Top up"}
}
```

Response:
- `201 Created` transaction details

## Internal transfer

- Method: `POST`
- Path: `/api/v1/transactions/transfer/`
- Auth: `Bearer <access>`

Request body (JSON):

```json
{
  "from_reference_tag": "@wlt_x7k9f.1",
  "to_reference_tag": "@wlt_ab12cd.2",
  "amount": "5.00",
  "metadata": {"note": "Move funds"}
}
```

Response:
- `201 Created` transaction details

## P2P send (hold)

- Method: `POST`
- Path: `/api/v1/transactions/send/`
- Auth: `Bearer <access>`

Request body (JSON):

```json
{
  "from_reference_tag": "@wlt_x7k9f.1",
  "to_reference_tag": "@wlt_z9y8x7.3",
  "amount": "7.00",
  "metadata": {"note": "Lunch"}
}
```

Response:
- `201 Created` transaction details (P2P is created as `pending` with hold)

## P2P action (accept/reject)

- Method: `POST`
- Path: `/api/v1/transactions/{tx_id}/action/`
- Auth: `Bearer <access>` (recipient only)

Request body (JSON):

```json
{
  "is_accepted": true
}
```

Response:
- `200 OK` updated transaction details

## Notes

- Transfers now use wallet `reference_tag` instead of internal IDs.
- `reference_tag` is generated automatically for each wallet and returned in wallet responses.
- Daily/per‑transaction limits apply based on `WALLET_LIMITS` settings.
- Transaction history endpoints support filtering by `wallet_tag`:
  - `/api/v1/transactions/?wallet_tag=@wlt_x7k9f.1`
