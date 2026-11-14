import json
import os
import random
import torch
import torch.nn as nn
import torch.optim as optim

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FireRecoveryNeuralNet(nn.Module):
    def __init__(self, input_dim=6):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 24)
        self.fc2 = nn.Linear(24, 12)
        self.fc3 = nn.Linear(12, 2)  # [erosion_risk, recovery_score]

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return torch.sigmoid(self.fc3(x))


def build_dataset(n_samples=1500):
    random.seed(303)
    X_raw, y = [], []
    for _ in range(n_samples):
        slope = random.uniform(0.03, 0.95)
        ndvi = random.uniform(0.10, 0.85)
        aridity = random.uniform(0.15, 0.95)
        rain_intensity = random.uniform(0.05, 0.95)
        canopy_heat = random.uniform(0.30, 0.98)
        moisture = random.uniform(0.06, 0.42)

        erosion_risk = max(0.05, min(0.97, 0.50 * slope + 0.30 * (1.0 - ndvi) + 0.22 * rain_intensity + random.gauss(0, 0.02)))
        recovery_score = max(0.08, min(0.96, 0.48 * ndvi + 0.35 * (1.0 - aridity) + 0.18 * moisture + random.gauss(0, 0.02)))

        X_raw.append([slope, ndvi, aridity, rain_intensity, canopy_heat, moisture])
        y.append([erosion_risk, recovery_score])

    X_t = torch.tensor(X_raw, dtype=torch.float32)
    mean = X_t.mean(dim=0)
    std = X_t.std(dim=0).clamp(min=1e-5)
    X_norm = (X_t - mean) / std
    return X_norm, torch.tensor(y, dtype=torch.float32), mean.tolist(), std.tolist()


def train():
    X, y, mean, std = build_dataset()
    model = FireRecoveryNeuralNet(input_dim=6)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.006)

    for epoch in range(1, 141):
        optimizer.zero_grad()
        loss = criterion(model(X), y)
        loss.backward()
        optimizer.step()
        if epoch % 35 == 0 or epoch == 1:
            print(f"[Network 4 - Fire]  Epoch {epoch:3d}/140 | Loss: {loss.item():.5f}")

    torch.save(model.state_dict(), os.path.join(ROOT_DIR, "terrapulse_fire_model.pth"))
    with open(os.path.join(ROOT_DIR, "terrapulse_fire_preprocess.json"), "w", encoding="utf-8") as f:
        json.dump({"features": ["slope", "ndvi", "aridity", "rain_intensity", "canopy_heat", "moisture"], "mean": mean, "std": std}, f, indent=2)
    print("Saved Network 4 weights & terrapulse_fire_preprocess.json")


if __name__ == "__main__":
    train()