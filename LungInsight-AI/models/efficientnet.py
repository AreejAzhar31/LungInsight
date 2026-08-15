"""
EfficientNet-B3 model for binary chest X-ray classification (NORMAL vs PNEUMONIA).

Uses torchvision's EfficientNet-B3 backbone, pretrained on ImageNet
(the ONLY pretrained weights used anywhere in this project — everything else,
including the classifier head, is trained from scratch on the chest X-ray data).

Supports:
    - transfer learning (frozen backbone, train only the head)
    - fine-tuning (unfreeze backbone after N epochs, lower LR)
"""

from __future__ import annotations
import torch
import torch.nn as nn
from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights


class PneumoniaClassifier(nn.Module):
    def __init__(self, num_classes: int = 2, pretrained: bool = True, dropout: float = 0.3):
        super().__init__()
        weights = EfficientNet_B3_Weights.IMAGENET1K_V1 if pretrained else None
        backbone = efficientnet_b3(weights=weights)

        # torchvision EfficientNet: `features` (conv stack) + `avgpool` + `classifier`
        in_features = backbone.classifier[1].in_features
        backbone.classifier = nn.Identity()  # we replace the head below

        self.backbone = backbone  # exposes .features, .avgpool
        self.head = nn.Sequential(
            nn.Dropout(p=dropout, inplace=True),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.backbone.features(x)
        x = self.backbone.avgpool(x)
        x = torch.flatten(x, 1)
        return self.head(x)

    # ---- transfer learning helpers -------------------------------------

    def freeze_backbone(self):
        for p in self.backbone.features.parameters():
            p.requires_grad = False

    def unfreeze_backbone(self):
        for p in self.backbone.features.parameters():
            p.requires_grad = True

    def trainable_parameters(self):
        return [p for p in self.parameters() if p.requires_grad]


def build_model(cfg) -> PneumoniaClassifier:
    model_cfg = cfg.model
    model = PneumoniaClassifier(
        num_classes=model_cfg.num_classes,
        pretrained=model_cfg.pretrained,
        dropout=model_cfg.dropout,
    )
    if model_cfg.freeze_backbone_epochs > 0:
        model.freeze_backbone()
    return model
