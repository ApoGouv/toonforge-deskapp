from pipelines.base_pipeline import BasePipeline
from pipelines.cv.cv_pipeline import CVPipeline
from pipelines.ai.animegan_pipeline import AnimeGANPipeline


class PipelineManager:
    """
    Owns the active pipeline and exposes its capabilities.
    """

    def __init__(self):

        self.pipelines = {
            "cv": CVPipeline,
            "animegan": AnimeGANPipeline,
        }

        self._logger = None
        self._pipeline_key = "cv"
        self._pipeline: BasePipeline = self.pipelines[self._pipeline_key]()

    # ---- Pipeline access ----
    @property
    def pipeline(self) -> BasePipeline:
        return self._pipeline

    def set_logger(self, logger_callable):
        """
        Attach a logger function that will be injected
        into all pipeline instances.
        """
        self._logger = logger_callable

        # Inject into current pipeline immediately
        if self._pipeline:
            self._pipeline.set_logger(logger_callable)


    def set_pipeline(self, key: str):
        if key not in self.pipelines:
            raise ValueError(f"Unknown pipeline: {key}")

        self._pipeline_key = key
        self._pipeline: BasePipeline = self.pipelines[key]()

        # Inject logger automatically if it exists
        if self._logger:
            self._pipeline.set_logger(self._logger)

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
