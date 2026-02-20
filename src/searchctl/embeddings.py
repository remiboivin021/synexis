from __future__ import annotations

from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str, device: str):
        self.model = SentenceTransformer(model_name, device=None if device == "auto" else device)

    def encode_passages(self, texts: Iterable[str], batch_size: int) -> np.ndarray:
        prefixed = [f"passage: {t}" for t in texts]
        vectors = self.model.encode(prefixed, batch_size=batch_size, convert_to_numpy=True)
        return l2_normalize(vectors)

    def encode_query(self, text: str) -> np.ndarray:
        vec = self.model.encode([f"query: {text}"], convert_to_numpy=True)
        return l2_normalize(vec)[0]


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms
