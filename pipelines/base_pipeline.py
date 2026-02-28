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
    
    def set_option(self, name: str, value):
        raise NotImplementedError(
            f"{type(self).__name__} does not support options"
        )
    
    @property
    def has_image(self):
        return self.image is not None

    def get_preview_image(self, scale=0.4):
        """
        Default behavior: resize original image.
        Pipelines may override.
        """
        if not self.has_image:
            return None

        import cv2
        h, w = self.image.shape[:2]
        return cv2.resize(
            self.image,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA
        )
    