"""MobileNetV3-Large transfer-learning classifier.

Training (scripts/train.py) freezes the ImageNet backbone, extracts a 1280-d
embedding per image once, and fits only a small linear head on top - the
fastest way to fine-tune on a CPU. At save time backbone + head are written
into a single checkpoint so inference works fully offline.
"""
from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from . import config

torch.set_num_threads(max(1, os.cpu_count() or 1))

EMBED_DIM = 1280

TRANSFORM = transforms.Compose([
    transforms.Resize((config.IMG_SIZE, config.IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(config.IMAGENET_MEAN, config.IMAGENET_STD),
])


def build_backbone(pretrained: bool = True) -> nn.Module:
    weights = models.MobileNet_V3_Large_Weights.IMAGENET1K_V2 if pretrained else None
    net = models.mobilenet_v3_large(weights=weights)
    # Keep features -> pool -> Linear(960, 1280) -> Hardswish; drop the ImageNet output layer
    net.classifier = nn.Sequential(net.classifier[0], net.classifier[1])
    return net


def build_head(num_classes: int, kind: str = "mlp") -> nn.Module:
    """'mlp' (one hidden layer) generalises better to field photos than 'linear'."""
    if kind == "linear":
        return nn.Sequential(nn.Dropout(0.2), nn.Linear(EMBED_DIM, num_classes))
    return nn.Sequential(nn.Dropout(0.3), nn.Linear(EMBED_DIM, 512), nn.ReLU(),
                         nn.Dropout(0.3), nn.Linear(512, num_classes))


class AgriVisionNet(nn.Module):
    def __init__(self, num_classes: int, pretrained_backbone: bool = False, head_kind: str = "mlp"):
        super().__init__()
        self.backbone = build_backbone(pretrained_backbone)
        self.head = build_head(num_classes, head_kind)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x))


class Classifier:
    """Loads the trained checkpoint and returns calibrated class probabilities."""

    def __init__(self, path=config.MODEL_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Trained model not found at {path}. Run scripts/train.py first."
            )
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        self.classes: list[str] = ckpt["classes"]
        self.temperature: float = float(ckpt.get("temperature", 1.0))
        self.metrics: dict = ckpt.get("metrics", {})
        # Field photos are harder, so they get their own (stricter) abstention threshold
        self.field_threshold: float = float(ckpt.get("field_threshold", config.CONFIDENCE_THRESHOLD))
        self.net = AgriVisionNet(len(self.classes), head_kind=ckpt.get("head", "linear"))
        self.net.load_state_dict(ckpt["state_dict"])
        self.net.eval()

    @torch.inference_mode()
    def predict(self, rgb: np.ndarray) -> np.ndarray:
        x = TRANSFORM(Image.fromarray(rgb)).unsqueeze(0)
        logits = self.net(x)[0] / self.temperature
        return torch.softmax(logits, dim=0).numpy()
