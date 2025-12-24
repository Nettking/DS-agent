# Agent pipeline with Streamlit UI

## Quickstart
1. Build and start the stack:
   ```bash
   docker compose up --build
   ```
2. Open the control panel at http://localhost:8501 to view state and run steps.
3. Verify LocalAI models are available at http://localhost:8080/v1/models.
4. Set `LOCALAI_MODEL` in `.env` to one of the models returned by the LocalAI endpoint.
