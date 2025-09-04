from __future__ import annotations

import cProfile
import pstats
from pathlib import Path

import numpy as np
import pandas as pd

from openworld_specialty_chemicals.chemistry import fit_parameters


def _make_df(n: int = 10_000) -> pd.DataFrame:
    t = np.arange(0, n, dtype=float) / 10.0
    c0, k = 100.0, 0.05
    c = c0 * np.exp(-k * t)
    return pd.DataFrame({"time": t, "species": ["SO4"] * len(t), "concentration": c})


def main() -> None:
    df = _make_df()
    prof = cProfile.Profile()
    prof.enable()
    fit_parameters(df, "SO4")
    prof.disable()
    dump = Path("artifacts/profile_chemistry.prof")
    dump.parent.mkdir(parents=True, exist_ok=True)
    prof.dump_stats(str(dump))
    print(f"Wrote {dump}")
    stats = pstats.Stats(prof).strip_dirs().sort_stats("tottime")
    stats.print_stats(15)


if __name__ == "__main__":
    main()

