"""PyTorch Dataset & Augmentations for Solar Filament Segmentation.

Loads solar disk patches with Hann tiling and solar physics augmentations.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset

from solar_filament_2026.data_loader import create_synthetic_solar_disk


class SolarFilamentDataset(Dataset):
    """Dataset serving normalized solar disk patches and binary target masks."""

    def __init__(
        self,
        samples: List[Tuple[np.ndarray, np.ndarray]],
        augment: bool = True,
        patch_size: int = 256,
    ) -> None:
        self.samples = samples
        self.augment = augment
        self.patch_size = patch_size

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        img, mask = self.samples[idx]

        # Random crop to patch size if image is larger
        h, w = img.shape[:2]
        if h > self.patch_size and w > self.patch_size:
            top = np.random.randint(0, h - self.patch_size)
            left = np.random.randint(0, w - self.patch_size)
            img = img[top:top + self.patch_size, left:left + self.patch_size]
            mask = mask[top:top + self.patch_size, left:left + self.patch_size]

        # Augmentation
        if self.augment:
            if np.random.rand() > 0.5:
                img = np.fliplr(img).copy()
                mask = np.fliplr(mask).copy()
            if np.random.rand() > 0.5:
                img = np.flipud(img).copy()
                mask = np.flipud(mask).copy()
            k = np.random.randint(0, 4)
            if k > 0:
                img = np.rot90(img, k).copy()
                mask = np.rot90(mask, k).copy()

        # Convert to float32 tensors (1, H, W)
        img_tensor = torch.from_numpy(img).float().unsqueeze(0)
        mask_tensor = torch.from_numpy(mask.astype(np.float32)).unsqueeze(0)
        return img_tensor, mask_tensor


def create_mock_training_dataset(num_samples: int = 16, seed: int = 42) -> SolarFilamentDataset:
    """Generate synthetic dataset for quick training verification."""
    samples = []
    for i in range(num_samples):
        disk, filaments = create_synthetic_solar_disk(shape=(256, 256), num_filaments=3, seed=seed + i)
        combined_mask = np.zeros((256, 256), dtype=bool)
        for f in filaments:
            combined_mask |= f
        samples.append((disk, combined_mask))
    return SolarFilamentDataset(samples, augment=True, patch_size=256)
