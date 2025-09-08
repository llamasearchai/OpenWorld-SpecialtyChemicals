#!/usr/bin/env python3
from __future__ import annotations

import os

import numpy as np
import pandas as pd


def main() -> None:
    os.makedirs("data", exist_ok=True)
    t = np.arange(0, 50, dtype=float)
    c = 12.0 * np.exp(-0.05 * t) + np.random.default_rng(7).normal(0, 0.2, size=t.size)
    df = pd.DataFrame({"time": t, "species": ["SO4"] * len(t), "concentration": c})
    df.to_csv("data/lab_batch.csv", index=False)
    print("Wrote data/lab_batch.csv")


if __name__ == "__main__":
    main()


