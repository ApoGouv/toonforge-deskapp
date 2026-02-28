from pipelines.pipeline_manager import PipelineManager


class PipelineController:
    """
    Mediates between UI and the active pipeline.
    Keeps pipeline-specific logic out of the UI.
    """

    def __init__(self, manager: PipelineManager):
        self.manager = manager

    @property
    def pipeline(self):
        return self.manager.pipeline

    # ---------------------------
    # Generic option setter
    # ---------------------------
    def set_option(self, name: str, value):
        pipeline = self.pipeline
        if pipeline is None:
            return

        pipeline.set_option(name, value)

    def get_preview_image(self, scale=0.4):
        pipeline = self.pipeline
        if not pipeline or not pipeline.has_image:
            return None
        
        return pipeline.get_preview_image(scale)
    
    def process(self, preview=False):
        pipeline = self.pipeline
        if pipeline is None or not pipeline.has_image:
            raise RuntimeError("No image loaded")

        if preview:
            if not pipeline.supports_preview:
                raise RuntimeError("Preview not supported")

            img = pipeline.get_preview_image()
            return pipeline.process_preview(img)

        # Full processing
        return pipeline.combine()


            