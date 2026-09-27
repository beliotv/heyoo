# beliotv/heyoo

Fork of https://github.com/Neurotech-HQ/heyoo with these fixes:

- `requests-toolbelt>=1.0.0` so urllib3 2.x no longer raises `cannot import name 'appengine'`
- Removed unused `MultipartEncoder` import in `heyoo/__init__.py`
- Graph API version from `WHATSAPP_API_VERSION` (default `v21.0`)
- Webhook secrets from env: `TOKEN`, `PHONE_NUMBER_ID`, `VERIFY_TOKEN`
- Docker: Python 3.11 + gunicorn, installs this tree (`pip install -e .`)
- Webhook returns 200 even on handler errors so Meta does not retry-storm

```bash
git clone https://github.com/beliotv/heyoo.git
cd heyoo
cp .env.example .env
# fill TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN
docker compose build --no-cache && docker compose up
```
