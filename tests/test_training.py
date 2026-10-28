"""Unit Tests for Solar Filament Training Subsystem.

Verifies:
1. ResidualUNet architecture forward pass and tensor dimensions.
2. CompoundFilamentLoss computation and backpropagation gradient flow.
3. Dataset loading, preprocessing, and batch collation.
4. Trainer execution, epoch step, and validation metrics computation.
5. Model checkpoint serialization and reloadability.
"""

from pathlib import Path
import tempfile
import torch
from torch.utils.data import DataLoader
import pytest

from solar_filament_2026.training.models import ResidualUNet, CompoundFilamentLoss
from solar_filament_2026.training.dataset import SolarFilamentDataset, create_mock_training_dataset
from solar_filament_2026.training.trainer import SolarFilamentTrainer


def test_residual_unet_forward():
    """Verify ResidualUNet handles arbitrary input dimensions with correct output shapes."""
    model = ResidualUNet(in_channels=1, out_channels=1, base_ch=16)
    x = torch.randn(2, 1, 128, 128)
    logits = model(x)
    assert logits.shape == (2, 1, 128, 128), f"Expected shape (2, 1, 128, 128), got {logits.shape}"
    assert not torch.isnan(logits).any(), "Model logits contain NaN"


def test_compound_filament_loss_and_gradients():
    """Verify CompoundFilamentLoss computes scalar loss and backpropagates valid gradients."""
    model = ResidualUNet(in_channels=1, out_channels=1, base_ch=8)
    criterion = CompoundFilamentLoss(bce_weight=0.5, tversky_weight=1.0, lovasz_weight=1.0)

    x = torch.randn(2, 1, 64, 64)
    target = (torch.rand(2, 1, 64, 64) > 0.8).float()

    logits = model(x)
    loss = criterion(logits, target)

    assert isinstance(loss, torch.Tensor)
    assert loss.dim() == 0, "Loss must be scalar"
    assert loss.item() > 0, "Loss should be positive"
    assert not torch.isnan(loss), "Loss is NaN"

    loss.backward()
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"Gradient is None for {name}"
            assert not torch.isnan(param.grad).any(), f"Gradient has NaN for {name}"


def test_dataset_and_dataloader():
    """Verify dataset items are formatted correctly as float tensors."""
    dataset = create_mock_training_dataset(num_samples=4, image_size=128, seed=42)
    assert len(dataset) == 4

    img, mask = dataset[0]
    assert img.shape == (1, 128, 128)
    assert mask.shape == (1, 128, 128)
    assert img.dtype == torch.float32
    assert mask.dtype == torch.float32
    assert 0.0 <= img.min() and img.max() <= 1.0

    loader = DataLoader(dataset, batch_size=2, shuffle=False)
    batch_img, batch_mask = next(iter(loader))
    assert batch_img.shape == (2, 1, 128, 128)
    assert batch_mask.shape == (2, 1, 128, 128)


def test_trainer_fit_and_checkpoint():
    """Verify full training fit loop and checkpoint saving."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        train_ds = create_mock_training_dataset(num_samples=4, image_size=64, seed=10)
        val_ds = create_mock_training_dataset(num_samples=2, image_size=64, seed=20)

        train_loader = DataLoader(train_ds, batch_size=2)
        val_loader = DataLoader(val_ds, batch_size=2)

        model = ResidualUNet(in_channels=1, out_channels=1, base_ch=8)
        trainer = SolarFilamentTrainer(model=model, device="cpu", learning_rate=1e-3)

        history = trainer.fit(train_loader, val_loader, epochs=2, save_dir=tmp_path)

        assert len(history) == 2
        assert "train_loss" in history[0]
        assert "val_iou" in history[0]

        ckpt_file = tmp_path / "best_filament_model.pt"
        assert ckpt_file.exists(), "Checkpoint file best_filament_model.pt was not saved"

        # Verify weights can be reloaded
        loaded_model = ResidualUNet(in_channels=1, out_channels=1, base_ch=8)
        state_dict = torch.load(ckpt_file, map_location="cpu")
        loaded_model.load_state_dict(state_dict)
        loaded_model.eval()

        test_out = loaded_model(torch.randn(1, 1, 64, 64))
        assert test_out.shape == (1, 1, 64, 64)
