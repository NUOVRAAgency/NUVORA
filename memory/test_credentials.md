# Test Credentials

## Admin Account
- Email: `admin@mergent.com`
- Password: `Admin@123`
- Role: `admin`
- Login endpoint: `POST /api/auth/login`
- Admin panel UI: `/admin`

## Notes
- Brand name is now **NUVORA** (the admin email/password keys are retained for backward compatibility).
- JWT token returned in response body AND set as httpOnly cookie `access_token`.
- Frontend stores token in localStorage as `mergent_token` and sends `Authorization: Bearer <token>` for cross-origin reliability.
- Default site contact info (editable from `/admin/settings`):
  - Phone/WhatsApp: `+1 (608) 979-3938`
  - Email: `nuvoranuvora760@gmail.com`
