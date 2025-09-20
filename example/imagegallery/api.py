import os
import tempfile
from aiohttp import web
from ucore_framework.web.http import HttpServer
from example.imagegallery.models import ImageRecord
from example.imagegallery.tasks import generate_thumbnail

def create_http_server(app):
    """Create and configure the HTTP server with routes"""
    http_server = HttpServer(app)

    @http_server.route("/", methods=["GET"])
    async def root(request):
        return web.json_response({
            "message": "UCore ImageGallery API",
            "endpoints": {
                "GET /images": "List all images",
                "POST /images": "Upload a new image (form-data with 'file' field)"
            },
            "version": "1.0.0"
        })

    @http_server.route("/images", methods=["GET"])
    async def list_images(request):
        images = await ImageRecord.find({})
        return web.json_response([{
            "id": str(img.get("_id")),
            "filename": img.get("filename"),
            "status": img.get("status"),
            "thumbnail_path": img.get("thumbnail_path"),
        } for img in images])

    @http_server.route("/images", methods=["POST"])
    async def upload_image(request):
        form = await request.form()
        file = form.get("file")
        if not file:
            return web.json_response({"error": "No file uploaded"}, status=400)
        # Save file to temp dir
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        # Create DB record
        record = ImageRecord.create(filename=file.filename, status="processing")
        await record.save()
        # Process thumbnail synchronously for demo purposes
        generate_thumbnail(str(record._id))
        return web.json_response({"id": str(record._id)}, status=201)
    
    return http_server
