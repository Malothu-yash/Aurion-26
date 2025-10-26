## Deploying AURION Backend to Render

Follow these steps to fix the common issues you saw in the logs (Mongo DB name NoneType error and "No open ports detected" port scan failure) and get a stable Render deployment.

### 1) Required environment variables (set in Render Dashboard)
Add these in your Render Service → Environment → Environment Variables (mark secrets as secret):

- `MONGODB_URL` (or `mongo_uri`) — full MongoDB connection string (Atlas). Example:
  `mongodb+srv://<user>:<password>@cluster0.mongodb.net/aurion?retryWrites=true&w=majority`
- `MONGODB_DB_NAME` (or `mongo_db_name`) — database name your app uses. Example: `aurion_auth`
- `JWT_SECRET_KEY` — long random secret used by the app (do not use default)
- `FRONTEND_URL` — your frontend URL, e.g. `https://your-frontend.vercel.app`
- `BASE_URL` — public backend URL, e.g. `https://your-backend.onrender.com`
- `ALLOWED_ORIGINS` — comma-separated allowed CORS origins, e.g.: `https://your-frontend.vercel.app,https://localhost:5173`

Optional / add if you use these features:
- `REDIS_URL` or `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`
- `SENDGRID_API_KEY`, `SENDER_EMAIL` or `MAIL_USERNAME`/`MAIL_PASSWORD`/`MAIL_FROM` for SMTP
- AI keys used by your app (OPENAI_API_KEY, GEMINI_API_KEY, etc.)

Important: do NOT put any of the above in the frontend (Vercel) unless they are intentionally public. Frontend envs must start with `VITE_`.

### 2) Start Command — bind to the correct port and host
Render requires your service to bind to `0.0.0.0:$PORT`. Edit your service settings and set the Start Command to one of the following (recommended):

Recommended (production, process manager):
```
gunicorn -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:$PORT --workers 2
```

Simple alternative:
```
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Do NOT use `--reload` in production (it also tends to bind on localhost).

If your service currently runs `start_server.py`, Render may be launching Uvicorn with `--host 127.0.0.1`. Replace that behavior by explicitly using the Start Command above in Render settings.

### 3) Redeploy & verify
1. Save env vars and the new Start Command in Render UI. Trigger a new deploy (Manual Deploy or push to the branch).
2. Watch logs in the Render Dashboard. The server should start and you should see lines like:
   - `Uvicorn running on http://0.0.0.0:<port>`
   - `✅ MongoDB connected successfully`

3. Test the health endpoint:
```
curl https://<your-render-service>.onrender.com/health
```
Expected output: JSON with status "healthy" and HTTP 200.

### 4) Troubleshooting Mongo issues
- If the logs still show `name must be an instance of str, not <class 'NoneType'>` or `MongoDB connection failed`:
  - Double-check the **exact env var names** in Render: `MONGODB_URL` (or `mongo_uri`) and `MONGODB_DB_NAME` (or `mongo_db_name`) must be present and non-empty.
  - Confirm you did not accidentally include quotes around the values in the Render UI.
  - If using MongoDB Atlas, ensure the cluster allows connections from Render (whitelist / network access). For quick testing set access to 0.0.0.0/0 (not for production long-term).

### 5) Logs & common fixes
- If Render says "No open ports detected" it means the process bound to `127.0.0.1` or a fixed port instead of `$PORT` on `0.0.0.0`. Fix the Start Command as shown above.
- If you see `AutoReconnect` or `ConnectionResetError`, check credentials, Atlas network whitelist, and consider temporarily increasing serverSelectionTimeoutMS in `init_mongodb()`.

### 6) Optional: add a `render.yaml`
You can define your service with `render.yaml` for reproducible deployments. Example snippet (do NOT commit secrets):

```yaml
services:
  - type: web
    name: aurion-backend
    env: python
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:$PORT --workers 2
    healthCheckPath: /health
```

Set secrets using the Render dashboard (do not put them in the YAML file).

---
If you want, I can: create a `render.yaml` in this repo (without secrets) and/or validate your current Render service settings if you paste them here. Which would you like? (I can also walk you through the Render UI clicks step-by-step.)
