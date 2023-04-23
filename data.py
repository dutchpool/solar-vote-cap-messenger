import json
from typing import Dict

DATA_FILE_NAME = "data.json"

try:
    data = json.load(open(DATA_FILE_NAME, "r"))
except Exception:
    data = {}


def get_last_activation_timestamp() -> int:
    return data["last_activation_timestamp"] if "last_activation_timestamp" in data else 0


def set_last_activation_timestamp(timestamp: int):
    data["last_activation_timestamp"] = timestamp
    save_data()


def get_activations() -> Dict[str, int]:
    return data["activations"] if "activations" in data else {}


def set_activations(activations: Dict[str, int]):
    data["activations"] = activations
    save_data()


def save_data():
    with open(DATA_FILE_NAME, "w+") as outfile:
        json.dump(data, outfile, default=vars)
