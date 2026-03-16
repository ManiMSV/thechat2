# ChatApp Backend

This folder contains the FastAPI backend for ChatApp as described in `PRD-ChatApp.md`.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy or edit `.env` and provide a MongoDB connection string and JWT secret. A sample `.env` is included.
4. Run the server:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`.  A health check endpoint exists at `/health`.

## Endpoints
See `routers` modules for implementation.  Basic auth, users, conversations, messages and WebSocket functionality have been implemented according to the PRD.

## Notes
- The WebSocket route is `/ws/{conversation_id}`; supply a `token` query parameter carrying a valid JWT.
- The MongoDB database used is `thechat` by default.
