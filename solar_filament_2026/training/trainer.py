"""Training Orchestrator and Cross-Validation Loop.

Executes training with AdamW, CosineAnnealingLR, CompoundFilamentLoss,
and checkpoint management.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader

from solar_filament_2026.training.dataset import SolarFilamentDataset, create_mock_training_dataset
from solar_filament_2026.training.models import CompoundFilamentLoss, ResidualUNet

logger = logging.getLogger("filament.training")


class SolarFilamentTrainer:
    """Trains ResidualUNet using Compound Loss and validates convergence."""

    def __init__(
        self,
        model: Optional[torch.nn.Module] = None,
        device: str = "cpu",
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
    ) -> None:
        self.device = torch.device(device if (torch.cuda.is_available() and device == "cuda") else "cpu")
        self.model = model or ResidualUNet(in_channels=1, out_channels=1, base_ch=16)
        self.model.to(self.device)

        self.criterion = CompoundFilamentLoss(bce_weight=0.5, tversky_weight=1.0, lovasz_weight=1.0)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    def train_epoch(self, dataloader: DataLoader) -> float:
        """Run one training epoch and return mean loss."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for images, targets in dataloader:
            images = images.to(self.device)
            targets = targets.to(self.device)

            self.optimizer.zero_grad()
            logits = self.model(images)
            loss = self.criterion(logits, targets)
            loss.backward()
            self.optimizer.step()

            total_loss += float(loss.item())
            num_batches += 1

        return total_loss / max(1, num_batches)

    def validate_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
        """Evaluate model on validation dataloader and compute loss + IoU."""
        self.model.eval()
        total_loss = 0.0
        total_iou = 0.0
        num_batches = 0

        with torch.no_grad():
            for images, targets in dataloader:
                images = images.to(self.device)
                targets = targets.to(self.device)

                logits = self.model(images)
                loss = self.criterion(logits, targets)
                probs = torch.sigmoid(logits)
                preds = probs > 0.5

                # Compute IoU
                intersection = (preds & (targets > 0.5)).sum().float()
                union = (preds | (targets > 0.5)).sum().float()
                iou = (intersection + 1e-6) / (union + 1e-6)

                total_loss += float(loss.item())
                total_iou += float(iou.item())
                num_batches += 1

        return {
            "val_loss": total_loss / max(1, num_batches),
            "val_iou": total_iou / max(1, num_batches),
        }

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 3,
        save_dir: Optional[Path] = None,
        use_scheduler: bool = True,
    ) -> List[Dict[str, float]]:
        """Run full training loop and return history."""
        save_path = save_dir or (Path(os.getcwd()) / "solar_filament_2026" / "models")
        save_path.mkdir(parents=True, exist_ok=True)

        scheduler = None
        if use_scheduler and epochs > 1:
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=epochs, eta_min=1e-5
            )

        history = []
        best_loss = float("inf")
        best_iou = -1.0

        for epoch in range(1, epochs + 1):
            t0 = time.time()
            train_loss = self.train_epoch(train_loader)
            val_metrics = self.validate_epoch(val_loader)
            if scheduler is not None:
                scheduler.step()
            elapsed = time.time() - t0

            current_lr = self.optimizer.param_groups[0]["lr"]
            record = {
                "epoch": epoch,
                "train_loss": round(train_loss, 4),
                "val_loss": round(val_metrics["val_loss"], 4),
                "val_iou": round(val_metrics["val_iou"], 4),
                "lr": round(current_lr, 6),
                "time_s": round(elapsed, 2),
            }
            history.append(record)

            logger.info(
                f"Epoch [{epoch}/{epochs}] - Train Loss: {train_loss:.4f} | "
                f"Val Loss: {val_metrics['val_loss']:.4f} | Val IoU: {val_metrics['val_iou']:.4f} | LR: {current_lr:.6f} ({elapsed:.1f}s)"
            )

            # Checkpoint best model if val loss or val IoU improves
            improved = False
            if val_metrics["val_loss"] < best_loss:
                best_loss = val_metrics["val_loss"]
                improved = True
            if val_metrics["val_iou"] > best_iou:
                best_iou = val_metrics["val_iou"]
                improved = True

            if improved:
                torch.save(self.model.state_dict(), save_path / "best_filament_model.pt")

        return history
