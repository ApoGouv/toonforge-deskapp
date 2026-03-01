from .base_pipeline import BasePipeline
from .cv_pipeline import CVPipeline


class PipelineManager:
    """
    Owns the active pipeline and exposes its capabilities.
    """

    def __init__(self):
        # Default pipeline (current behavior)
        self._pipeline: BasePipeline = CVPipeline()

    # ---- Pipeline access ----
    @property
    def pipeline(self) -> BasePipeline:
        return self._pipeline

    def set_pipeline(self, pipeline: BasePipeline):
        self._pipeline = pipeline

    # ---- Capability proxies ----
    @property
    def supports_preview(self) -> bool:
        return self._pipeline.supports_preview

    @property
    def supports_options(self) -> bool:
        return self._pipeline.supports_options

    @property
    def supports_presets(self) -> bool:
        return self._pipeline.supports_presets

    # ---- Image ----
    def set_image(self, image):
        self._pipeline.set_image(image)
