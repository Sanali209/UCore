from abc import ABC, abstractmethod
from UCoreFrameworck.fs.models import AnnotationRecord, FileRecord

class AnnotationJob(ABC):
    """
    Abstract base class for annotation jobs.
    Annotation jobs process files and add annotation records.
    """
    @abstractmethod
    async def run(self, file_record: FileRecord, annotation_data: dict):
        """
        Run the annotation job on a file.
        Args:
            file_record (FileRecord): The file to annotate.
            annotation_data (dict): Annotation parameters.
        """
        pass

class AvgRatingAnnotationJob(AnnotationJob):
    """
    Example annotation job for average rating.
    """
    async def run(self, file_record: FileRecord, annotation_data: dict):
        """
        Run average rating annotation logic (placeholder).
        """
        pass

class SingleLabelAnnotationJob(AnnotationJob):
    """
    Example annotation job for single label.
    """
    async def run(self, file_record: FileRecord, annotation_data: dict):
        """
        Run single label annotation logic (placeholder).
        """
        pass

# Registry for annotation jobs
annotation_job_registry = {}

def register_annotation_job(name: str, job: AnnotationJob):
    """
    Register an annotation job by name.
    Args:
        name (str): Job name.
        job (AnnotationJob): Job instance.
    """
    annotation_job_registry[name] = job

# Register example jobs
register_annotation_job("avg_rating", AvgRatingAnnotationJob())
register_annotation_job("single_label", SingleLabelAnnotationJob())

def get_annotation_job(name: str) -> AnnotationJob:
    """
    Get an annotation job by name.
    Args:
        name (str): Job name.
    Returns:
        AnnotationJob
    """
    return annotation_job_registry[name]
