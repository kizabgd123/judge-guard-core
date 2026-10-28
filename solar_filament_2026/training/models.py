"""Deep Learning Architecture & Compound Losses for Solar Filament Segmentation.

Implements ResidualUNet and CompoundFilamentLoss (Lovasz + Focal Tversky + BCE).
Optimized for thin curvilinear flux ropes and high Panoptic Quality (PQ).
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# SOTA Segmentation Losses
# ---------------------------------------------------------------------------

def _lovasz_grad(gt_sorted: torch.Tensor) -> torch.Tensor:
    """Compute gradient of the Lovasz extension with respect to sorted errors."""
    p = len(gt_sorted)
    gts = gt_sorted.sum()
    intersection = gts - gt_sorted.float().cumsum(0)
    union = gts + (1.0 - gt_sorted.float()).cumsum(0)
    jaccard = 1.0 - intersection / torch.clamp(union, min=1.0)
    if p > 1:
        jaccard[1:p] = jaccard[1:p] - jaccard[0:-1]
    return jaccard


def lovasz_hinge_flat(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """Compute Lovasz hinge loss on flattened logits and binary targets."""
    if len(targets) == 0:
        return logits.sum() * 0.0

    signs = 2.0 * targets.float() - 1.0
    errors = 1.0 - logits * signs
    errors_sorted, perm = torch.sort(errors, dim=0, descending=True)
    perm = perm.data
    gt_sorted = targets[perm]
    grad = _lovasz_grad(gt_sorted)
    loss = torch.dot(F.relu(errors_sorted), grad)
    return loss


def lovasz_sigmoid_loss(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """Multi-dimensional Lovasz-Sigmoid loss for binary filament segmentation."""
    return lovasz_hinge_flat(logits.view(-1), targets.view(-1))


def focal_tversky_loss(
    logits: torch.Tensor,
    targets: torch.Tensor,
    alpha: float = 0.7,
    beta: float = 0.3,
    gamma: float = 1.33,
    smooth: float = 1.0,
) -> torch.Tensor:
    """Focal Tversky loss emphasizing recall on thin filament spines."""
    probs = torch.sigmoid(logits).view(-1)
    targets_flat = targets.view(-1).float()

    true_pos = (probs * targets_flat).sum()
    false_neg = ((1.0 - probs) * targets_flat).sum()
    false_pos = (probs * (1.0 - targets_flat)).sum()

    tversky = (true_pos + smooth) / (true_pos + alpha * false_neg + beta * false_pos + smooth)
    return torch.pow(1.0 - tversky, gamma)


class CompoundFilamentLoss(nn.Module):
    """Compound loss combining BCE, Focal Tversky, and Lovasz-Sigmoid."""

    def __init__(
        self,
        bce_weight: float = 0.5,
        tversky_weight: float = 1.0,
        lovasz_weight: float = 1.0,
    ) -> None:
        super().__init__()
        self.bce_weight = bce_weight
        self.tversky_weight = tversky_weight
        self.lovasz_weight = lovasz_weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, targets.float())
        tversky = focal_tversky_loss(logits, targets)
        lovasz = lovasz_sigmoid_loss(logits, targets)
        return self.bce_weight * bce + self.tversky_weight * tversky + self.lovasz_weight * lovasz


# ---------------------------------------------------------------------------
# Residual U-Net Architecture
# ---------------------------------------------------------------------------

class _ConvBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
        self.residual = nn.Conv2d(in_ch, out_ch, kernel_size=1, bias=False) if in_ch != out_ch else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x) + self.residual(x)


class ResidualUNet(nn.Module):
    """Deep Residual U-Net for solar filament instance segmentation."""

    def __init__(self, in_channels: int = 1, out_channels: int = 1, base_ch: int = 16) -> None:
        super().__init__()
        self.inc = _ConvBlock(in_channels, base_ch)
        self.down1 = nn.Sequential(nn.MaxPool2d(2), _ConvBlock(base_ch, base_ch * 2))
        self.down2 = nn.Sequential(nn.MaxPool2d(2), _ConvBlock(base_ch * 2, base_ch * 4))
        self.down3 = nn.Sequential(nn.MaxPool2d(2), _ConvBlock(base_ch * 4, base_ch * 8))

        self.up2 = nn.ConvTranspose2d(base_ch * 8, base_ch * 4, kernel_size=2, stride=2)
        self.conv_up2 = _ConvBlock(base_ch * 8, base_ch * 4)

        self.up1 = nn.ConvTranspose2d(base_ch * 4, base_ch * 2, kernel_size=2, stride=2)
        self.conv_up1 = _ConvBlock(base_ch * 4, base_ch * 2)

        self.up0 = nn.ConvTranspose2d(base_ch * 2, base_ch, kernel_size=2, stride=2)
        self.conv_up0 = _ConvBlock(base_ch * 2, base_ch)

        self.outc = nn.Conv2d(base_ch, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x0 = self.inc(x)
        x1 = self.down1(x0)
        x2 = self.down2(x1)
        x3 = self.down3(x2)

        d2 = self.conv_up2(torch.cat([self.up2(x3), x2], dim=1))
        d1 = self.conv_up1(torch.cat([self.up1(d2), x1], dim=1))
        d0 = self.conv_up0(torch.cat([self.up0(d1), x0], dim=1))
        return self.outc(d0)
