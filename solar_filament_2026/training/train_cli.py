"""Command-Line Interface for Solar Filament Model Training.

Usage:
    python3 solar_filament_2026/training/train_cli.py --epochs 3 --batch-size 4 --device cpu
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add repo root to sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import torch
from torch.utils.data import DataLoader

from solar_filament_2026.training.dataset import create_mock_training_dataset
from solar_filament_2026.training.models import ResidualUNet
from solar_filament_2026.training.trainer import SolarFilamentTrainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Solar Filament ResidualUNet Baseline.")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--device", type=str, default="cpu", help="Compute device: cpu or cuda")
    parser.add_argument("--no-scheduler", action="store_true", help="Disable learning rate cosine annealing scheduler")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 65)
    print("🚀 Solar Filament 2026 — ResidualUNet Training Session")
    print(f"   Epochs: {args.epochs} | Batch Size: {args.batch_size} | Device: {args.device} | Scheduler: {not args.no_scheduler}")
    print("=" * 65)

    # Prepare datasets
    print("Preparing training & validation datasets...")
    train_dataset = create_mock_training_dataset(num_samples=16, seed=42)
    val_dataset = create_mock_training_dataset(num_samples=8, seed=99)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)

    model = ResidualUNet(in_channels=1, out_channels=1, base_ch=16)
    trainer = SolarFilamentTrainer(model=model, device=args.device, learning_rate=args.lr)

    start_t = time.time()
    history = trainer.fit(train_loader, val_loader, epochs=args.epochs, use_scheduler=not args.no_scheduler)
    total_time = time.time() - start_t

    print("=" * 65)
    print(f"✅ Training completed in {total_time:.2f}s")
    for rec in history:
        lr_str = f" | LR = {rec['lr']:.6f}" if "lr" in rec else ""
        print(f"   Epoch {rec['epoch']}: Train Loss = {rec['train_loss']:.4f} | Val Loss = {rec['val_loss']:.4f} | Val IoU = {rec['val_iou']:.4f}{lr_str}")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
