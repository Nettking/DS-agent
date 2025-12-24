# Agent pipeline with Streamlit UI

## Quickstart
1. Build and start the stack:
   ```bash
   docker compose up -d --build
   ```
2. Open the control panel at http://localhost:8501 to view state and run steps.
3. Verify LocalAI models are available at http://localhost:8080/v1/models.
4. Set `LOCALAI_MODEL` in `.env` to one of the models returned by the LocalAI endpoint.

### Hard rebuild after code changes
If Docker is using cached layers and you need to ensure new code is picked up:
```bash
docker compose down
docker compose build --no-cache ui mvp
docker compose up -d
```

If your LocalAI backend supports enforced JSON responses, set `FORCE_JSON=1` in `.env` to request `response_format: json_object`.
