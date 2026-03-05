import cv2
import numpy as np
from pipelines.ai.model_loader import ModelLoader


class AnimeGANModel:
    """
    Handles AnimeGAN ONNX inference.
    """

    def __init__(self, model_path: str):
        self.session = ModelLoader.load_model(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    # ---------------------------
    # Preprocess
    # ---------------------------
    def preprocess(self, img):
        """
        Prepare BGR OpenCV image for AnimeGAN.
        """
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img = img.astype(np.float32) / 127.5 - 1.0  # normalize to [-1,1]

        # NHWC - [batch, height, width, channels]
        img = np.expand_dims(img, axis=0)           # add batch

        return img

    # ---------------------------
    # Postprocess
    # ---------------------------
    def postprocess(self, output):
        """
        Convert model output back to OpenCV BGR image.
        """
        output = np.squeeze(output)  # remove batch
        
        output = (output + 1.0) * 127.5
        output = np.clip(output, 0, 255).astype(np.uint8)

        output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        
        return output

    # ---------------------------
    # Inference
    # ---------------------------
    def run(self, img):
        input_tensor = self.preprocess(img)
        output = self.session.run(
            [self.output_name],
            {self.input_name: input_tensor},
        )[0]

        return self.postprocess(output)