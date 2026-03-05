from abc import ABC, abstractmethod
import cv2

from ui.panels.options.empty_options_panel import EmptyOptionsPanel


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
        self.logger = None  # optional logging callback

    # ---- Lifecycle ----
    def set_image(self, image):
        self.image = image

    @property
    def has_image(self):
        return self.image is not None
    
    # ---------- UI Hook ----------

    def set_logger(self, logger_callable):
        self.logger = logger_callable

    def create_options_panel(self, parent):
        """
        Return a Tk Frame containing pipeline-specific options.
        Return EmptyOptionsPanel if no options are supported.
        """
        return EmptyOptionsPanel(parent, self)

    # ---- Processing API ----
    @abstractmethod
    def process(self, settings: dict):
        """
        Full processing.
        Must return:
        {
            "final": image,
            "steps": dict[str, image]   # optional
        }
        """
        pass

    def preview(self, settings: dict):
        """
        Optional preview.
        Pipelines that support preview override this.
        Same return format as process().
        """
        raise NotImplementedError("Preview not supported by this pipeline")

    def set_option(self, name: str, value):
        raise NotImplementedError(f"{type(self).__name__} does not support options")

    def get_preview_image(self, scale=0.4):
        """
        Default behavior: resize original image.
        Pipelines may override.
        """
        if not self.has_image:
            return None

        h, w = self.image.shape[:2]
        return cv2.resize(
            self.image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
        )
