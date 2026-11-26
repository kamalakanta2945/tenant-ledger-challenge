Install dependencies: `python -m pip install -r requirements.txt`
Start: `python -m uvicorn app.main:app --reload`
Tests: `python -m pytest -q`
Swagger: open `http://127.0.0.1:8000/docs`
Use header `X-Tenant-API-Key: tenant-a-demo-key` or `tenant-b-demo-key` for demo tenants.
