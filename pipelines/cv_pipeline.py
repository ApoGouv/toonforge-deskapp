import cv2
import numpy as np

from .base_pipeline import BasePipeline

class CVPipeline(BasePipeline):
    supports_preview = True
    supports_options = True
    supports_presets = True

    def __init__(self):
        super().__init__()

        # ---- Caches ----
        self._denoised = None
        self._gray = None
        self._edges = None
        self._smoothed = None
        self._quantized = None

        # ---- Parameters (defaults tuned for richer colors) ----
        self.smooth_passes = 5
        self.num_colors = 20
        self.edge_block = 9
        self.edge_C = 2

        self.smooth_mode = "bilateral" # bilateral, stylization, gaussian, median
        self.color_mode = "kmeans"     # options: kmeans, posterize, mediancut, octree
        self.blend_mode = "hard"       # hard, mask, overlay
        self.use_denoise = False

    # ---------------------------
    # Image lifecycle
    # ---------------------------
    def set_image(self, image):
        self.image = image
        self.invalidate_all()

    @property
    def has_image(self):
        return self.image is not None
    
    # ---------------------------
    # Base Image Logic (Caching Denoise)
    # ---------------------------
    def get_base_image(self):
        """Returns the denoised image if enabled, otherwise the original."""
        if not self.use_denoise:
            return self.image
        
        if self._denoised is None:
            # Only runs when denoising is toggled ON and cache is empty
            # h=10 is a good balance for removing grain without destroying detail
            self._denoised = cv2.fastNlMeansDenoisingColored(
                self.image, None, 10, 10, 7, 21
            )
        return self._denoised

    def process(self, settings: dict):
        return self.combine();

    def preview(self, settings: dict):
        return self.process_preview(settings["image"])
    
    def set_option(self, name: str, value):
        match name:
            case "denoise":
                self.use_denoise = value
                self.invalidate_denoise()

            case "edge_block":
                self.edge_block = value
                self.invalidate_edges()

            case "blend_mode":
                self.blend_mode = value

            case "smooth_mode":
                self.smooth_mode = value
                self.invalidate_smoothing()
                self.invalidate_quantization()

            case "smooth_passes":
                self.smooth_passes = value
                self.invalidate_smoothing()
                self.invalidate_quantization()

            case "color_mode":
                self.color_mode = value
                self.invalidate_quantization()

            case "num_colors":
                self.num_colors = value
                self.invalidate_quantization()

            case _:
                raise ValueError(f"Unknown CVPipeline option: {name}")

    # ---------------------------
    # Individual Steps
    # ---------------------------
    def _get_raw_gray(self):
        """Returns a basic grayscale version of the base image without any blurring."""
        return cv2.cvtColor(self.get_base_image(), cv2.COLOR_BGR2GRAY)

    def compute_gray(self):
        if self._gray is None:
            raw_gray = self._get_raw_gray()
            self._gray = cv2.medianBlur(raw_gray, 7)
        return self._gray

    def compute_edges(self):
        gray = self.compute_gray() # Uses cached gray

        if self._edges is None:
            blockSize = max(3, self.edge_block)
            if blockSize % 2 == 0: blockSize += 1
          
            self._edges = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                blockSize=blockSize,
                C=self.edge_C
            )

            # Clean up noise from edges - remove salt and pepper
            self._edges = cv2.medianBlur(self._edges, 3)

        return self._edges

    def compute_smoothing(self):
        if self._smoothed is None:
            img = self.get_base_image().copy() # Start from denoised/original base

            if self.smooth_mode == "bilateral":
                for _ in range(self.smooth_passes):
                    img = cv2.bilateralFilter(
                        img,
                        d=9,
                        sigmaColor=50 + self.smooth_passes * 20,
                        sigmaSpace=50 + self.smooth_passes * 20
                    )

            elif self.smooth_mode == "stylization":
                img = cv2.stylization(
                    img,
                    sigma_s=40 + self.smooth_passes * 5,
                    sigma_r=0.4 + self.smooth_passes * 0.02
                )

            elif self.smooth_mode == "gaussian":
                k = max(3, self.smooth_passes * 2 + 1)
                img = cv2.GaussianBlur(img, (k, k), 0)

            elif self.smooth_mode == "median":
                k = max(3, self.smooth_passes * 2 + 1)
                img = cv2.medianBlur(img, k)

            self._smoothed = img

        return self._smoothed

    # ---------------------------
    # Color Quantization Methods
    # ---------------------------
    def quantize_kmeans(self, img):

        # Performance Trick: Resize down to find clusters, then apply to large image
        h, w = img.shape[:2]
        small_img = cv2.resize(img, (200, 200), interpolation=cv2.INTER_AREA)
        data = np.float32(small_img).reshape((-1, 3))

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 0.1)
        _, _, centers = cv2.kmeans(
            data, 
            self.num_colors, 
            None, 
            criteria, 
            5, 
            cv2.KMEANS_RANDOM_CENTERS
        )
        
        # Apply clusters to the original full-size image
        centers = np.uint8(centers)
        full_data = np.float32(img).reshape((-1, 3))
        
        # Efficiently map every pixel to the nearest center
        distances = np.linalg.norm(full_data[:, np.newaxis] - centers, axis=2)
        labels = np.argmin(distances, axis=1)

        return centers[labels].reshape((h, w, 3))

    def quantize_posterize(self, img):
        # Approximate total colors using per-channel levels
        levels = int(round(self.num_colors ** (1/3)))
        levels = max(2, min(16, levels))

        factor = 256 // levels
        return (img // factor) * factor

    def quantize_median_cut(self, img):
        # Uses OpenCV’s color quantization via k-means-like histogram clustering
        # Convert to 1D list of pixels
        Z = img.reshape((-1, 3))
        Z = np.float32(Z)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = self.num_colors
        _, labels, centers = cv2.kmeans(Z, K, None, criteria, 3, cv2.KMEANS_PP_CENTERS)

        centers = np.uint8(centers)
        return centers[labels.flatten()].reshape(img.shape)

    def quantize_octree(self, img):
        # Fast color reduction using kmeans with fewer iterations
        data = np.float32(img).reshape((-1, 3))
        _, labels, centers = cv2.kmeans(
            data,
            self.num_colors,
            None,
            (cv2.TERM_CRITERIA_EPS, 5, 1.0),
            1,
            cv2.KMEANS_PP_CENTERS
        )
        centers = np.uint8(centers)
        return centers[labels.flatten()].reshape(img.shape)


    def boost_vibrancy(self, img, saturation=1.5, brightness=1.1):
        # Convert to HSV to boost color without messing up the shadows
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype("float32")
        hsv[:, :, 1] *= saturation  # Saturation
        hsv[:, :, 2] *= brightness  # Value/Brightness
        hsv[:, :, 1:] = np.clip(hsv[:, :, 1:], 0, 255)
        return cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)


    # ---------------------------
    # Quantization Dispatcher
    # ---------------------------
    def compute_quantization(self):
        smoothed = self.compute_smoothing()

        if self._quantized is None:
            if self.color_mode == "kmeans":
                self._quantized = self.quantize_kmeans(smoothed)
                # self._quantized = self.boost_vibrancy(self._quantized)

            elif self.color_mode == "posterize":
                self._quantized = self.quantize_posterize(smoothed)

            elif self.color_mode == "mediancut":
                self._quantized = self.quantize_median_cut(smoothed)

            elif self.color_mode == "octree":
                self._quantized = self.quantize_octree(smoothed)

            else:
                raise ValueError(f"Unknown color mode: {self.color_mode}")

        return self._quantized

    def compute_pencil_sketch(self):
        """Creates a professional pencil sketch look using division blending."""
        gray = self._get_raw_gray()
        
        # Invert the gray image
        inverted = 255 - gray
        
        # Blur the inverted image significantly
        # Use edge_block to determine blur intensity!
        k_size = max(3, self.edge_block * 2 + 1) 
        blurred = cv2.GaussianBlur(inverted, (k_size, k_size), 0)
        
        # Mix the gray and blurred-inverted using a 'Divide' blend
        sketch = cv2.divide(gray, 255 - blurred, scale=256)

        # Convert back to BGR so it fits the rest of the pipeline
        return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

    def combine(self):
        # Check if we are in Pencil Sketch mode (triggered by specific blend/color combo)
        if self.color_mode == "sketch":
            sketch = self.compute_pencil_sketch()
            # Return same structure so UI doesn't crash
            return sketch, self._get_raw_gray(), sketch, sketch, sketch

        gray = self.compute_gray()
        edges = self.compute_edges()
        quantized = self.compute_quantization()
        
        # Boost vibrancy of colors BEFORE blending with black edges
        quantized = self.boost_vibrancy(quantized)

        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        if self.blend_mode == "hard":
            cartoon = cv2.bitwise_and(quantized, edges_colored)

        elif self.blend_mode == "mask":
            # Mask: ensure edges are crisp black
            mask = cv2.threshold(edges, 128, 255, cv2.THRESH_BINARY)[1]
            cartoon = cv2.bitwise_and(quantized, quantized, mask=mask)

        elif self.blend_mode == "overlay":
            # Use a "Multiply" style blend for a comic book feel
            # This keeps the colors bright but layers the lines on top
            cartoon = cv2.addWeighted(quantized, 1.0, edges_colored, 0.2, -50)

        else:
            raise ValueError(f"Unknown blend mode: {self.blend_mode}")

        return cartoon, gray, edges_colored, self._smoothed, self._quantized

    def process_preview(self, image):
        """
        Run the pipeline on a scaled image without polluting main caches.
        """
        temp = self._clone_for_image(image)
        return temp.combine()
    
    def _clone_for_image(self, image):
        clone = self.__class__()
        clone.set_image(image)

        # Copy relevant state
        clone.smooth_passes = self.smooth_passes
        clone.num_colors = self.num_colors
        clone.edge_block = self.edge_block
        clone.edge_C = self.edge_C
        clone.smooth_mode = self.smooth_mode
        clone.color_mode = self.color_mode
        clone.blend_mode = self.blend_mode
        clone.use_denoise = self.use_denoise

        return clone

    # ---------------------------
    # Cache Invalidation
    # ---------------------------
    def invalidate_denoise(self):
        self._denoised = None
        self.invalidate_all() # Everything depends on the base image

    def invalidate_gray(self):
        self._gray = None
        self.invalidate_edges()

    def invalidate_edges(self):
        self._edges = None

    def invalidate_smoothing(self):
        self._smoothed = None
        self._quantized = None

    def invalidate_quantization(self):
        self._quantized = None

    def invalidate_all(self):
        self._gray = None
        self._edges = None
        self._smoothed = None
        self._quantized = None