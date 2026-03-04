from pipelines.base_pipeline import BasePipeline
from pipelines.pipeline_step import PipelineStep


class AnimeGANPipeline(BasePipeline):
    """
    AI-based anime/cartoon stylization pipeline (CPU-friendly).
    """
    supports_preview = True
    supports_options = False
    supports_presets = False

     # ---------------------------
    # Preview
    # ---------------------------
    def preview(self):
        """
        Preview runs on a scaled-down image to keep CPU usage low.
        """
        if not self.has_image:
            raise RuntimeError("No image set for AnimeGAN pipeline")

        img = self.image

        # Get scaled down image for preview
        preview_img = self.get_preview_image(0.4)

        return self._run(preview_img)

    # ---------------------------
    # Full process
    # ---------------------------
    def process(self, preview=False):
        """
        Full-resolution processing.
        """
        if not self.has_image:
            raise RuntimeError("No image set for AnimeGAN pipeline")

        return self._run(self.image)

    # ---------------------------
    # Internal shared logic
    # ---------------------------
    def _run(self, img):
        """
        TEMP stub: just echo input.
        Later this is where the AI model runs.
        """

        steps = [
            PipelineStep(
                key="input",
                label="Original Input",
                image=img,
                tooltip="Original image before AI stylization.",
            )
        ]

        return {
            "steps": steps,
            "final": img,
        }