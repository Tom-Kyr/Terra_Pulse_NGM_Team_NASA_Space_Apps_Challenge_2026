import os
import random
import torch
import torch.nn as nn
import torch.optim as optim

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WaterStressNeuralNet(nn.Module):
    def __init__(self, input_dim=6):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out = self.relu(self.fc1(x))
        out = self.relu(self.fc2(out))
        return self.sigmoid(self.fc3(out))


def build_dataset(n_samples=1500):
    random.seed(42)
    X, y = [], []
    for _ in range(n_samples):
        temp = random.uniform(0.15, 0.98)       # Normalized temperature
        precip = random.uniform(0.0, 0.95)      # Normalized precipitation
        moisture = random.uniform(0.05, 0.55)   # Volumetric soil moisture
        ndvi = random.uniform(0.15, 0.90)       # MODIS NDVI
        slope = random.uniform(0.02, 0.90)      # SRTM slope
        et0 = min(1.0, temp * 0.72 + (1.0 - moisture) * 0.28)

        # Hydrological water stress target (0..1)
        stress = max(0.02, min(0.98, 0.45 * temp + 0.40 * (1.0 - moisture / 0.55) - 0.22 * precip + 0.12 * et0 + random.gauss(0, 0.02)))
        X.append([temp, precip, moisture, ndvi, slope, et0])
        y.append([stress])
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


def train():
    X, y = build_dataset()
    model = WaterStressNeuralNet(input_dim=6)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.008)

    for epoch in range(1, 121):
        optimizer.zero_grad()
        preds = model(X)
        loss = criterion(preds, y)
        loss.backward()
        optimizer.step()
        if epoch % 30 == 0 or epoch == 1:
            print(f"[Network 1 - Water] Epoch {epoch:3d}/120 | Loss: {loss.item():.5f}")

    out_path = os.path.join(ROOT_DIR, "terrapulse_water_model.pth")
    torch.save(model.state_dict(), out_path)
    print(f"Saved Network 1 weights -> {out_path}")


if __name__ == "__main__":
    train()