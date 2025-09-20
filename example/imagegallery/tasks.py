import time
from celery import Celery
from example.imagegallery.models import ImageRecord

celery_app = Celery("imagegallery", broker="redis://localhost:6379/0")

@celery_app.task
def generate_thumbnail(image_id: str):
    # Simulate image processing
    time.sleep(2)
    # Fetch and update the image record
    record = ImageRecord.collection().find_one({"_id": image_id})
    if record:
        ImageRecord.collection().update_one(
            {"_id": image_id},
            {"$set": {"status": "completed", "thumbnail_path": f"/thumbnails/{image_id}.jpg"}}
        )
