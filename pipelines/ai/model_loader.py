import onnxruntime as ort
import os


class ModelLoader:
    """
    Handles ONNX model loading and caching.
    """

    _sessions = {}

    @classmethod
    def load_model(cls, model_path: str):
        """
        Load ONNX model once and cache session.
        """
        if model_path in cls._sessions:
            return cls._sessions[model_path]

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ONNX model not found: {model_path}")

        session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )

        cls._sessions[model_path] = session
        return session