# ImageGallery: UCore Web API & Background Worker Example

This example demonstrates:
- REST API with file upload
- MongoDB data modeling
- Celery background processing
- Resource and component management

## Setup

1. **Install dependencies:**
   ```
   pip install celery pymongo aiohttp
   ```

2. **Start MongoDB and Redis locally.**

3. **Start the Celery worker:**
   ```
   celery -A example.imagegallery.tasks.celery_app worker --loglevel=info
   ```

4. **Run the API server:**
   ```
   python main.py
   ```

## API

- `POST /images` — Upload an image (multipart/form-data, field: `file`)
- `GET /images` — List all images and their status

## Files

- `main.py` — App setup and run
- `api.py` — HTTP routes and logic
- `models.py` — ImageRecord data model
- `tasks.py` — Celery background task
- `config.yml` — Example config

## Example Workflow

1. Upload an image via API.
2. The image is saved and a DB record is created with status "processing".
3. Celery worker simulates thumbnail generation and updates the record to "completed".
4. Query `/images` to see status and thumbnail path.
