#!/usr/bin/env python3
"""
showplot_speed_size.py

- Forces non-interactive Agg backend to avoid GUI/back-end hangs.
- If results TSV exists (default: ./results.tsv) it will plot that data:
    columns expected: method, level, percent, mb_s
  Otherwise it uses embedded example arrays (your original data).
- Saves PNG (default: ./results.png). Does not call plt.show().
"""
from pathlib import Path
import argparse
import csv
import sys

# Force headless backend before importing seaborn/pyplot
import matplotlib
matplotlib.use("Agg")

import seaborn as sns
import matplotlib.pyplot as plt
sns.set(style="whitegrid")

def plot_from_arrays(series_list, out_path, title=None):
    """
    series_list: list of tuples (label, x_array, y_array)
    """
    plt.figure(figsize=(10,6))
    ax = plt.gca()
    for label, x, y in series_list:
        # ensure plain Python lists for seaborn/matplotlib
        ax = sns.lineplot(x=list(x), y=list(y), marker="o", linewidth=2, label=label, ax=ax)
    ax.set_xlabel("Speed (MB/s)")
    ax.set_ylabel("Compressed size (%)")
    if title:
        ax.set_title(title)
    ax.legend(title="Method", loc="best")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def read_tsv_and_build_series(infile):
    """
    Expect TSV with columns: method, level, percent, mb_s
    We'll produce one series per method, sorted by level ascending.
    Returns list of (label, x_array, y_array)
    """
    print(f"Reading TSV: {infile}")
    rows = []
    with open(infile, newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        if reader.fieldnames is None:
            raise RuntimeError("TSV has no header")
        for i, r in enumerate(reader, start=1):
            try:
                method = (r.get("method") or r.get("Method") or "").strip()
                level = int(r.get("level") or r.get("Level") or 0)
                percent = float(r.get("percent") or r.get("%") or r.get("Percent") or 0.0)
                mb_s = float(r.get("mb_s") or r.get("mb/s") or r.get("MB/s") or 0.0)
                rows.append({"method": method, "level": level, "percent": percent, "mb_s": mb_s})
            except Exception as e:
                print(f"[WARN] skipping malformed row {i}: {e}", file=sys.stderr, flush=True)
    if not rows:
        raise RuntimeError("No usable rows in TSV")
    # group by method and build arrays sorted by level
    groups = {}
    for r in rows:
        groups.setdefault(r["method"], []).append(r)
    series = []
    for method, items in sorted(groups.items()):
        items_sorted = sorted(items, key=lambda x: x["level"])
        xs = [it["mb_s"] for it in items_sorted]
        ys = [it["percent"] for it in items_sorted]
        print(f"Method '{method}': levels = {[it['level'] for it in items_sorted]}, xs={xs}, ys={ys}")
        series.append((method, xs, ys))
    return series

def main():
    parser = argparse.ArgumentParser(description="Plot compression speed (MB/s) vs compressed size (%)")
    parser.add_argument("infile", nargs="?", default=None, help="Input TSV (default: ./results.tsv if present)")
    parser.add_argument("outfile", nargs="?", default=None, help="Output PNG (default: ./results.png)")
    args = parser.parse_args()

    scriptdir = Path(__file__).resolve().parent
    infile = Path(args.infile) if args.infile else scriptdir / "results.tsv"
    outfile = Path(args.outfile) if args.outfile else scriptdir / "results.png"

    # If TSV exists, plot from it; otherwise use embedded arrays (your original data)
    if infile.exists():
        try:
            series = read_tsv_and_build_series(infile)
            plot_from_arrays(series, outfile, title="Compression Speed vs Size")
            return
        except Exception as e:
            print(f"[ERROR] failed to read/plot TSV {infile}: {e}", file=sys.stderr, flush=True)
            print("[ERROR] falling back to embedded example data", file=sys.stderr, flush=True)
    else:
            print(f"[ERROR] Input file not found: {infile}", file=sys.stderr, flush=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
