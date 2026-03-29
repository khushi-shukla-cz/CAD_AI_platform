CAD AI Platform

This project analyzes STL files and returns geometry metadata plus validation insights.

Current modules
- Backend API: FastAPI service for STL upload, parsing, and validation
- Frontend MVP: React + Vite UI to upload STL and display API response

Backend run
1. Open a terminal in backend
2. Install dependencies:
	pip install -r requirements.txt
3. Start API:
	uvicorn main:app --reload --host 127.0.0.1 --port 8000
4. API docs:
	http://127.0.0.1:8000/docs

Frontend run
1. Open a terminal in frontend
2. Install dependencies:
	npm install
3. Create env file from example:
	copy .env.example .env.local
4. (Optional) Change API endpoint in .env.local:
	VITE_API_URL=http://127.0.0.1:8000/api/v1/analyze
5. Start development server:
	npm run dev
6. Open:
	http://127.0.0.1:5173

Environment config (Vite)
- API base endpoint is read from VITE_API_URL
- Default fallback if env is missing:
	http://127.0.0.1:8000/api/v1/analyze
- Recommended files:
	frontend/.env.local (local dev)
	frontend/.env.development (shared dev defaults)
	frontend/.env.production (production build)

Notes
- CORS is currently open for local development.
- Upload field accepts .stl files and sends multipart/form-data with field name file.
