import json
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from core.config import BASE_DIR


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


def load_json_file(filename: str):
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning reading {filename}: {e}")
    return {}


def load_pth_weights(filename: str):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {filename} not found.")
        return None
    try:
        obj = torch.load(path, map_location=torch.device("cpu"))
        print(f"Loaded PyTorch model: {filename}")
        return obj
    except Exception as e:
        print(f"Warning loading {filename}: {e}")
        return None


def normalize_features(raw_vals, preprocess_cfg):
    if not preprocess_cfg:
        return raw_vals
    mean = preprocess_cfg.get("mean") or preprocess_cfg.get("scaler_mean")
    scale = preprocess_cfg.get("std") or preprocess_cfg.get("scale") or preprocess_cfg.get("scaler_scale")
    if isinstance(mean, list) and isinstance(scale, list) and len(mean) == len(scale):
        n = min(len(raw_vals), len(mean))
        out = list(raw_vals)
        for i in range(n):
            s = scale[i] if scale[i] != 0 else 1.0
            out[i] = (raw_vals[i] - mean[i]) / s
        return out
    return raw_vals


def run_generic_pth_inference(pth_obj, feature_vector, expected_outputs=2):
    if pth_obj is None:
        return None
    try:
        with torch.no_grad():
            if isinstance(pth_obj, nn.Module):
                pth_obj.eval()
                x = torch.tensor([feature_vector], dtype=torch.float32)
                out = torch.sigmoid(pth_obj(x)).squeeze(0).tolist()
                return out if isinstance(out, list) else [out]

            if isinstance(pth_obj, dict):
                sd = pth_obj.get("state_dict", pth_obj)
                weight_keys = [k for k in sd.keys() if k.endswith(".weight") and sd[k].ndim == 2]
                if not weight_keys:
                    return None
                first_in = sd[weight_keys[0]].shape[1]
                vec = list(feature_vector[:first_in])
                while len(vec) < first_in:
                    vec.append(0.5)
                x = torch.tensor([vec], dtype=torch.float32)
                for idx, wk in enumerate(weight_keys):
                    bk = wk[:-7] + ".bias"
                    w = sd[wk]
                    b = sd.get(bk, torch.zeros(w.shape[0]))
                    x = F.linear(x, w, b)
                    if idx < len(weight_keys) - 1:
                        x = F.relu(x)
                x = torch.sigmoid(x).squeeze(0).tolist()
                if not isinstance(x, list):
                    x = [x]
                if len(x) >= expected_outputs:
                    return x[:expected_outputs]
    except Exception as e:
        print(f"Inference fallback triggered: {e}")
    return None


# Initialize all 4 network artifacts once at startup
water_model = WaterStressNeuralNet(input_dim=6)
water_loaded = False
water_path = os.path.join(BASE_DIR, "terrapulse_water_model.pth")
if os.path.exists(water_path):
    try:
        water_model.load_state_dict(torch.load(water_path, map_location=torch.device("cpu")))
        water_model.eval()
        water_loaded = True
        print("Loaded PyTorch model: terrapulse_water_model.pth")
    except Exception as e:
        print(f"Network 1 load fallback: {e}")

soil_pth = load_pth_weights("terrapulse_soil_model.pth")
soil_preprocess = load_json_file("terrapulse_soil_preprocess.json")

rotation_pth = load_pth_weights("terrapulse_rotation_model.pth")

fire_pth = load_pth_weights("terrapulse_fire_model.pth")
fire_preprocess = load_json_file("terrapulse_fire_preprocess.json")