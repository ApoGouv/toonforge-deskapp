from abc import ABC, abstractmethod

class BasePipeline(ABC):
    """
    Abstract pipeline interface.
    Each pipeline declares what it supports.
    """

    # ---- Capability flags ----
    supports_preview = False
    supports_options = False
    supports_presets = False

    def __init__(self):
        self.image = None

    # ---- Lifecycle ----
    def set_image(self, image):
        self.image = image

    # ---- Processing API ----
    @abstractmethod
    def process(self, settings: dict):
        """Run full processing and return final image"""
        pass

    def preview(self, settings: dict):
        """
        Optional preview.
        Pipelines that support preview override this.
        """
        raise NotImplementedError("Preview not supported by this pipeline")