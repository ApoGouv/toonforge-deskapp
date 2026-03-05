import cv2
from pipelines.base_pipeline import BasePipeline
from pipelines.pipeline_step import PipelineStep
from pipelines.ai.animegan_model import AnimeGANModel
from ui.panels.options.animegan_options_panel import AnimeGANOptionsPanel

class AnimeGANPipeline(BasePipeline):
    """
    AI-based anime/cartoon stylization pipeline using ONNX (CPU-friendly).
    """
    supports_preview = True
    supports_options = True
    supports_presets = False

    def __init__(self):
        super().__init__()

        self.models = {
            "Hayao": AnimeGANModel("models/animeganv2/AnimeGANv2_Hayao.onnx"),
            "Paprika": AnimeGANModel("models/animeganv2/AnimeGANv2_Paprika.onnx"),
            "Shinkai": AnimeGANModel("models/animeganv2/AnimeGANv2_Shinkai.onnx"),
        }
        self.selected_model = "Hayao"
        self.log_selected_model()
        

    def log_selected_model(self):
        if self.logger:
            self.logger(f"Selected model: {self.selected_model}")

    def set_option(self, name: str, value):
        if name == "model":
            if value in self.models:
                self.selected_model = value
                self.log_selected_model()
            else:
                raise ValueError(f"Unknown model: {value}")
            
    def create_options_panel(self, parent):
        return AnimeGANOptionsPanel(parent, self)

    # ---------------------------
    # Preview
    # ---------------------------
    def preview(self,  settings: dict):
        """
        Preview runs on a scaled-down image to keep CPU usage low.
        """
        image = settings.get("image")

        if image is None:
            raise RuntimeError("No preview image set")
        
        return self._run(image)

    # ---------------------------
    # Full process
    # ---------------------------
    def process(self, preview=False):
        """
        Full-resolution processing.
        """
        if not self.has_image:
            raise RuntimeError("No image set")

        return self._run()

    # ---------------------------
    # Internal shared logic
    # ---------------------------
    def _run(self, custom_image=None):
        model = self.models[self.selected_model]
        
        init_image = custom_image if custom_image is not None else self.image

        # Downscale safely
        prepared_img, original_size = self._prepare_image_for_model(init_image)

        # Run AI
        stylized_small = model.run(prepared_img)

        # Upscale back
        stylized_final = cv2.resize(stylized_small, original_size)

        steps = [
            PipelineStep(
                key="initial",
                label="Initial",
                image=init_image,
                tooltip="Initial input image",
            ),
            PipelineStep(
                key="downscaled",
                label="Downscaled",
                image=prepared_img,
                tooltip="Resized for model (memory-safe)",
            ),
            PipelineStep(
                key="stylized_small",
                label="Stylized (Model Output)",
                image=stylized_small,
                tooltip="Raw model output",
            ),
            PipelineStep(
                key="final",
                label="Final Stylized",
                image=stylized_final,
                tooltip="Upscaled to original resolution",
            ),
        ]

        return {
            "final": stylized_final,
            "steps": steps,
        }
    
    def _prepare_image_for_model(self, image, max_dim=1024):
         # Resize to multiple of 32 (required by AnimeGAN)
        h, w = image.shape[:2]

        if self.logger:
            self.logger(f"Original size: {w}x{h}")

        # Limit max dimension (max_dim): 1024 or 768 or 640
        scale = min(1.0, max_dim / max(h, w))
        new_w = int(w * scale)
        new_h = int(h * scale)

        # Limit max dimension: 1024 or 768 or 640
        def to_32(x):
            return 256 if x < 256 else x - x % 32

        # Make divisible by 32
        new_w = to_32(new_w)
        new_h = to_32(new_h)

        resized = cv2.resize(image, (new_w, new_h))

        if self.logger:
            self.logger(f"Processing size: {new_w}x{new_h}")

        return resized, (w, h)

        