from pipelines.pipeline_manager import PipelineManager
from pipelines.pipeline_step import PipelineStep


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

            preview_img = pipeline.get_preview_image()
            result = pipeline.preview({"image": preview_img})
        else:
            result = pipeline.process({})

        final = result["final"]
        steps = result.get("steps", [])

        # Enforce contract
        for step in steps:
            if not isinstance(step, PipelineStep):
                raise TypeError(
                    f"Expected PipelineStep, got {type(step).__name__}"
                )

        # Enforce contract
        return {"final": final, "steps": steps}

        steps = []

        # CVPipeline-specific mapping (kept OUT of the UI)
        if pipeline.__class__.__name__ == "CVPipeline":
            order = [
                ("gray", "Grayscale", "Convert image to grayscale for edge detection."),
                ("edges", "Edges", "Detect edges using adaptive thresholding."),
                ("smoothed", "Smoothing", "Smooth colors while preserving boundaries."),
                (
                    "quantized",
                    "Color Quantization",
                    "Reduce color palette for cartoon effect.",
                ),
                ("sketch", "Pencil Sketch", "Generate a pencil sketch rendering."),
            ]

            for key, label, tooltip in order:
                if key in raw_steps:
                    steps.append(
                        PipelineStep(
                            key=key, label=label, image=raw_steps[key], tooltip=tooltip
                        )
                    )

        else:
            # Generic fallback for future pipelines
            for key, img in raw_steps.items():
                steps.append(
                    PipelineStep(
                        key=key, label=key.replace("_", " ").title(), image=img
                    )
                )

        return steps
