# Digital Wallet

Backend API for a simple digital wallet system with users, wallets, and transactions.

## Quick start (local)

1) Copy the environment template:

```bash
cp .env.example .env
```

Leave `DB_HOST` empty in `.env` to use SQLite locally.

2) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

3) Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

API base: `http://127.0.0.1:8000/`

## Quick start (Docker + Postgres)

Set `DB_HOST=db` in your `.env` before starting.
If you want to expose Postgres on a different host port, set `DB_HOST_PORT` (the container always listens on 5432).

```bash
docker compose up --build
```

This runs migrations automatically and starts Django on `http://127.0.0.1:8000/`.

Environment variables used by Docker:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SECRET_KEY`

If `DB_HOST` is not set, the app uses SQLite (`db.sqlite3`).

## Configuration (.env)

Copy `.env.example` to `.env` and update secrets or DB credentials as needed.

## API examples

### API docs (Swagger)

Open: `http://127.0.0.1:8000/swagger/`  
Schema: `http://127.0.0.1:8000/api/schema/`

### Register

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+201234567890","first_name":"Mona","last_name":"Ibrahim","passcode":"123456","passcode_confirm":"123456"}'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+201234567890","password":"123456"}'
```

### Create wallet

```bash
curl -X POST http://127.0.0.1:8000/api/v1/wallets/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Primary","wallet_type":"current"}'
```

### Deposit (by reference tag)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/wallets/@wlt_x7k9f.1/deposit/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"amount":"10.00"}'
```

### Internal transfer

```bash
curl -X POST http://127.0.0.1:8000/api/v1/transactions/transfer/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"from_reference_tag":"@wlt_x7k9f.1","to_reference_tag":"@wlt_ab12cd.2","amount":"5.00"}'
```

### P2P send (hold)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/transactions/send/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"from_reference_tag":"@wlt_x7k9f.1","to_reference_tag":"@wlt_z9y8x7.3","amount":"7.00"}'
```

### P2P action (accept/reject)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/transactions/<tx_id>/action/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"is_accepted":true}'
```

### Transaction history

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/transactions/?wallet_tag=@wlt_x7k9f.1" \
  -H "Authorization: Bearer <access>"
```

## Design decisions

- **Reference tags**: Wallets expose a public `reference_tag` (e.g., `@wlt_x7k9f.1`) used for transfers instead of internal IDs.
- **Atomic money movement**: All balance changes go through `MoneyFlowService` with DB transactions + row locking.
- **Short-lived JWTs**: Access tokens expire quickly and are invalidated on passcode change via `token_version`.
- **Rolling access tokens**: Near-expiry tokens are rotated and returned in `X-Access-Token`.
- **Case-insensitive wallet names**: Uniqueness is enforced with a lower-cased unique constraint.
- **Configurable limits**: Per‑transaction and daily limits are configured via `WALLET_LIMITS`.
- **SQLite by default**: Postgres is used when `DB_HOST` is provided.

## Docs

More details in `docs/`:
- `docs/users.md`
- `docs/wallets.md`
- `docs/transactions.md`
