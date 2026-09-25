"""Compact PatchTST-style masked channel-independent Transformer.

Reimplementation, not the official benchmark configuration. Source:
https://arxiv.org/abs/2211.14730 and https://github.com/yuqinie98/PatchTST
Uses shared channel weights, temporal patch positions, no physical sensor IDs.
"""
from copy import deepcopy
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
import same_device_session_transfer as core


class PatchEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.project = nn.Linear(8, 32)
        self.position = nn.Parameter(torch.randn(8, 32) * .02)
        layer = nn.TransformerEncoderLayer(32, 4, 96, .1, activation='gelu',
                                           batch_first=True, norm_first=True)
        self.context = nn.TransformerEncoder(layer, 2, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(32)

    def patches(self, x):
        return x.transpose(1, 2).unfold(2, 8, 8).reshape(-1, 8, 8)

    def encode(self, patches):
        return self.norm(self.context(self.project(patches) + self.position))

    def forward(self, x):
        return self.encode(self.patches(x)).mean(1).reshape(len(x), x.shape[2], 32)


def pretrain(x, epochs, seed):
    core.seed_all(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    encoder, decoder = PatchEncoder().to(device), nn.Linear(32, 8).to(device)
    opt = torch.optim.AdamW(list(encoder.parameters()) + list(decoder.parameters()), lr=8e-4, weight_decay=1e-4)
    loader = DataLoader(TensorDataset(torch.from_numpy(x)), batch_size=64, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    history = []
    for _ in range(epochs):
        total = count = 0
        for (xb,) in loader:
            patches = encoder.patches(xb.to(device))
            # Exactly three of eight disjoint patches masked per channel (37.5%).
            ranks = torch.rand(patches.shape[:2], device=device).argsort(1).argsort(1)
            hidden = ranks < 3
            pred = decoder(encoder.encode(patches.masked_fill(hidden[..., None], 0)))
            loss = (pred[hidden] - patches[hidden]).square().mean()
            opt.zero_grad(set_to_none=True); loss.backward()
            nn.utils.clip_grad_norm_(list(encoder.parameters()) + list(decoder.parameters()), 2.)
            opt.step(); total += loss.item() * len(xb); count += len(xb)
        history.append(total / count)
    return deepcopy(encoder.state_dict()), history


def fit(x, y, vx, vy, state, epochs, seed):
    core.seed_all(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    encoder = PatchEncoder()
    encoder.load_state_dict(state)
    model = core.Regressor(encoder).to(device)
    opt = torch.optim.AdamW([{'params': model.encoder.parameters(), 'lr': 8e-5},
                            {'params': model.head.parameters(), 'lr': 8e-4}], weight_decay=2e-4)
    loader = DataLoader(TensorDataset(torch.from_numpy(x), torch.from_numpy(y / core.TARGET_SCALE)),
                        batch_size=min(64, len(x)), shuffle=True, generator=torch.Generator().manual_seed(seed))
    best, best_loss, history = None, float('inf'), []
    for epoch in range(epochs):
        model.train()
        for xb, yb in loader:
            loss = nn.functional.huber_loss(model(xb.to(device)), yb.to(device), delta=.1)
            opt.zero_grad(set_to_none=True); loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 2.); opt.step()
        model.eval()
        with torch.no_grad():
            value = nn.functional.huber_loss(model(torch.from_numpy(vx).to(device)),
                       torch.from_numpy(vy / core.TARGET_SCALE).to(device), delta=.1).item()
        history.append(value)
        if value < best_loss:
            best_loss, best = value, deepcopy(model.state_dict())
    model.load_state_dict(best)
    return model, {'validation_loss': history, 'best_validation_loss': best_loss}
