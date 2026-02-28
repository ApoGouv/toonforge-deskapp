from .base_pipeline import BasePipeline

class CVPipeline(BasePipeline):
    supports_preview = True
    supports_options = True
    supports_presets = True

    def process(self, settings: dict):
        raise NotImplementedError

    def preview(self, settings: dict):
        raise NotImplementedError