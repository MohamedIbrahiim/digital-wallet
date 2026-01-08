# Users API

Base path: `/api/v1/auth/`

## Register

- Method: `POST`
- Path: `/api/v1/auth/register/`
- Auth: None

Request body (JSON):

```json
{
  "mobile_number": "+201234567890",
  "first_name": "Mona",
  "last_name": "Ibrahim",
  "passcode": "123456",
  "passcode_confirm": "123456"
}
```

Response:
- `201 Created` with user data fields (as configured in serializer)

## Login

- Method: `POST`
- Path: `/api/v1/auth/login/`
- Auth: None

Request body (JSON):

```json
{
  "mobile_number": "+201234567890",
  "password": "123456"
}
```

Response:
- `200 OK` with `access` token (no refresh token)

## Change passcode

- Method: `POST`
- Path: `/api/v1/auth/change-passcode/`
- Auth: `Bearer <access>`

Request body (JSON):

```json
{
  "old_passcode": "123456",
  "new_passcode": "654321",
  "new_passcode_confirm": "654321"
}
```

Response:

```json
{
  "detail": "Passcode changed successfully."
}
```

Status: `200 OK`

## JWT time limitation

- Access token lifetime is 2 minutes (`SIMPLE_JWT.ACCESS_TOKEN_LIFETIME`).
- No refresh tokens are issued by the login endpoint.
- Token invalidation happens when `token_version` changes (e.g., after passcode change).
- Rolling token support: if the token is near expiry, a new access token is issued in
  the response header `X-Access-Token` when using authenticated endpoints.

Clients should:
- Attach `Authorization: Bearer <access>` on every request.
- Watch for `X-Access-Token` and replace the stored token when it appears.
