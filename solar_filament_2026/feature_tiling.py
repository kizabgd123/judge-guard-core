"""Hann-Window Sliding Tiling Engine.

Enables seamless tile decomposition and reconstruction for 2048x2048 images
without boundary seam artifacts or memory blowup on CPU.
"""

from __future__ import annotations

from typing import Generator, List, Tuple
import numpy as np


def create_2d_hann_window(height: int, width: int) -> np.ndarray:
    """Create a 2D Hann (cosine) blending window for smooth tile overlap."""
    wy = np.hanning(height)
    wx = np.hanning(width)
    window = np.outer(wy, wx).astype(np.float32)
    # Clamp minimum value to prevent division by zero near edges
    return np.maximum(window, 1e-4)


class HannTiler:
    """Sliding-window tile extractor and reconstructor."""

    def __init__(
        self,
        image_shape: Tuple[int, int] = (2048, 2048),
        tile_size: int = 512,
        overlap: int = 64,
    ) -> None:
        self.img_h, self.img_w = image_shape
        self.tile_size = tile_size
        self.overlap = overlap
        self.step = tile_size - overlap
        
        self.window = create_2d_hann_window(tile_size, tile_size)
        self.coords: List[Tuple[int, int, int, int]] = self._compute_tile_coords()

    def _compute_tile_coords(self) -> List[Tuple[int, int, int, int]]:
        """Compute top-left coordinates ensuring full coverage of image."""
        y_steps = list(range(0, self.img_h - self.tile_size + 1, self.step))
        if y_steps[-1] + self.tile_size < self.img_h:
            y_steps.append(self.img_h - self.tile_size)

        x_steps = list(range(0, self.img_w - self.tile_size + 1, self.step))
        if x_steps[-1] + self.tile_size < self.img_w:
            x_steps.append(self.img_w - self.tile_size)

        coords = []
        for y in y_steps:
            for x in x_steps:
                coords.append((y, x, y + self.tile_size, x + self.tile_size))
        return coords

    def extract_tiles(self, image: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """Extract all tiles with their bounding coordinates."""
        tiles = []
        for y1, x1, y2, x2 in self.coords:
            tile = image[y1:y2, x1:x2]
            tiles.append((tile, (y1, x1, y2, x2)))
        return tiles

    def reconstruct(self, tile_predictions: List[np.ndarray]) -> np.ndarray:
        """Blend probability tiles back into full image using Hann window weighting."""
        if len(tile_predictions) != len(self.coords):
            raise ValueError(f"Expected {len(self.coords)} tiles, got {len(tile_predictions)}")

        canvas = np.zeros((self.img_h, self.img_w), dtype=np.float32)
        weight_sum = np.zeros((self.img_h, self.img_w), dtype=np.float32)

        for pred, (y1, x1, y2, x2) in zip(tile_predictions, self.coords):
            canvas[y1:y2, x1:x2] += pred * self.window
            weight_sum[y1:y2, x1:x2] += self.window

        # Avoid zero division
        nonzero = weight_sum > 1e-6
        canvas[nonzero] /= weight_sum[nonzero]
        return canvas
