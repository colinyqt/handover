# Meter Tender Analysis & Recommendation System

## Overview
A modern Streamlit-based dashboard and backend for tender compliance and meter recommendation, supporting LLM/embedding model selection and ChromaDB semantic search.

## Local Development
1. Install Python 3.11+
2. `pip install -r requirements.txt`
3. `streamlit run overhaul/streamlit_app.py`

## Docker Deployment
1. Build the image:
   ```
   docker build -t meter-tender-app .
   ```
2. Run the container:
   ```
   docker run -p 8501:8501 --env-file .env meter-tender-app
   ```

## Environment Variables
See `.env.example` for required variables.

## Directory Structure
- `overhaul/streamlit_app.py` – Main UI
- `overhaul/core/` – Backend logic
- `overhaul/prompts/` – YAML pipelines
- `chroma_db/` – Vector DB (mounted or persistent)

## Notes
- For production, use a reverse proxy (nginx) for HTTPS.
- Do not commit secrets or large data files.
- For LLM/embedding model setup, see backend documentation.
