#!/usr/bin/env python3
"""
compress_bench.py

Benchmark compressors:
 - pigz variants found in ./exe/  (invoked as <exe> -<level> -c <infile>)
 - system gzip (shutil.which("gzip")) invoked as gzip -<level> -c <infile>
 - system zstd (shutil.which("zstd")) invoked as zstd -<level> -c <infile>

Behavior:
 - gzip/pigz levels default to [1,3,9] and are validated to 1..9
 - zstd levels default to [1,3,19] and are validated to 1..19
 - compressed files are written to tmp_compress_outputs/ then deleted immediately
 - writes results TSV: results.tsv (method, level, percent, mb_s, seconds, ...)
"""

from pathlib import Path
import argparse
import csv
import os
import shutil
import subprocess
import sys
import tarfile
import time

SCRIPT_DIR = Path(__file__).resolve().parent
EXE_DIR = SCRIPT_DIR / "exe"
GIT_URL = "https://github.com/MiloszKrajewski/SilesiaCorpus"
DATASET_DIR = Path("SilesiaCorpus")
TARBALL = Path("dataset.tar")
DEFAULT_GZIP_LEVELS = [1, 3, 6, 7, 9]       # for gzip / pigz (1..9)
DEFAULT_ZSTD_LEVELS = [1, 2, 3, 10, 19]      # for zstd (1..19)
OUTPREFIX = "results"
TMP_OUT_DIR = Path("tmp_compress_outputs")

def ensure_dataset_cloned():
    if DATASET_DIR.exists() and (DATASET_DIR / ".git").exists():
        print(f"{DATASET_DIR} exists; attempting git pull.")
        try:
            subprocess.run(["git", "-C", str(DATASET_DIR), "pull"], check=True)
        except subprocess.CalledProcessError:
            print("git pull failed; proceeding with existing copy.")
    else:
        print(f"Cloning {GIT_URL} into {DATASET_DIR} ...")
        subprocess.run(["git", "clone", GIT_URL], check=True)

    # unzip any .zip files if present
    for z in DATASET_DIR.glob("*.zip"):
        print(f"Unzipping {z} ...")
        try:
            subprocess.run(["unzip", "-o", z.name], cwd=str(DATASET_DIR), check=True)
            # Delete the .zip file after successful extraction
            z.unlink()
            print(f"Deleted {z}")
        except subprocess.CalledProcessError:
            print(f"Warning: unzip failed for {z}; skipping.")

def make_tarball(force=False):
    if TARBALL.exists() and not force:
        print(f"{TARBALL} exists; not recreating.")
        return
    if not DATASET_DIR.exists():
        raise RuntimeError(f"Dataset directory {DATASET_DIR} not found.")
    print(f"Creating tarball {TARBALL} ...")
    with tarfile.open(str(TARBALL), "w") as tar:
        for entry in sorted(DATASET_DIR.iterdir()):
            tar.add(str(entry), arcname=str(entry.name))
    print("Tarball created.")

def detect_exe_compressors():
    compressors = {}
    if not EXE_DIR.exists():
        return compressors
    for p in sorted(EXE_DIR.iterdir()):
        if p.is_file() and os.access(str(p), os.X_OK):
            compressors[p.name] = p
            print(f"Found local compressor: {p.name} -> {p}")
    return compressors

def detect_system_binary(name):
    return shutil.which(name)

def validate_levels(levels, min_level, max_level, name):
    for l in levels:
        if l < min_level or l > max_level:
            raise ValueError(f"Level {l} for {name} out of supported range [{min_level}..{max_level}]")

def run_and_capture(cmd_list, outpath):
    with open(outpath, "wb") as of:
        start = time.monotonic()
        proc = subprocess.run(cmd_list, stdout=of, stderr=subprocess.PIPE)
        end = time.monotonic()
        elapsed = end - start
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Compressor failed (rc={proc.returncode}): {stderr}")
    return elapsed

def safe_unlink(p: Path):
    try:
        if p.exists():
            p.unlink()
    except Exception as e:
        print(f"Warning: failed to delete {p}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Compression benchmark runner")
    parser.add_argument("--levels", nargs="+", type=int, default=None,
                        help="Compression levels to test for gzip/pigz (default: 1 3 9)")
    parser.add_argument("--zstd-levels", nargs="+", type=int, default=None,
                        help="Compression levels to test for zstd (default: 1 3 19)")
    parser.add_argument("--compressors", default=None,
                        help="Comma-separated list of compressors to test (labels: filenames in exe/ or 'gzip'/'zstd')")
    parser.add_argument("--out", default=OUTPREFIX, help="Output prefix (writes .tsv)")
    parser.add_argument("--recreate-tar", action="store_true", help="Recreate tarball even if present")
    parser.add_argument("--skip-clone", action="store_true", help="Skip cloning dataset")
    args = parser.parse_args()

    gzip_levels = args.levels if args.levels is not None else DEFAULT_GZIP_LEVELS
    zstd_levels = args.zstd_levels if args.zstd_levels is not None else DEFAULT_ZSTD_LEVELS

    # validate ranges
    try:
        validate_levels(gzip_levels, 1, 9, "gzip/pigz")
        validate_levels(zstd_levels, 1, 19, "zstd")
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)

    if not args.skip_clone:
        ensure_dataset_cloned()

    make_tarball(force=args.recreate_tar)
    original_size = TARBALL.stat().st_size
    original_mb = original_size / (1024 * 1024)
    print(f"Tarball: {TARBALL} size = {original_mb:.2f} MB")

    # Build compressors dictionary: label -> factory(level,infile,outfile) -> cmd_list
    compressors = {}

    # local pigz-like exes in exe/
    exe_comps = detect_exe_compressors()
    for label, pth in exe_comps.items():
        # local executables are pigz-like => support levels 1..9
        def make_factory(p=pth):
            def factory(level, infile, outfile):
                return [str(p), f"-{level}", "-c", str(infile)]
            return factory
        compressors[label] = {"factory": make_factory(), "type": "gzip-like"}

    # system gzip
    gzip_path = detect_system_binary("gzip")
    if gzip_path:
        def gzip_factory(level, infile, outfile):
            return [gzip_path, f"-{level}", "-c", str(infile)]
        compressors["gzip"] = {"factory": gzip_factory, "type": "gzip-like"}

    # system zstd
    zstd_path = detect_system_binary("zstd")
    if zstd_path:
        def zstd_factory(level, infile, outfile):
            return [zstd_path, f"-{level}", "-c", str(infile)]
        compressors["zstd"] = {"factory": zstd_factory, "type": "zstd"}

    if args.compressors:
        requested = [s.strip() for s in args.compressors.split(",") if s.strip()]
        # filter compressors dict to only requested that are present
        filtered = {}
        for r in requested:
            if r in compressors:
                filtered[r] = compressors[r]
            else:
                print(f"[WARN] requested compressor '{r}' not found; skipping")
        compressors = filtered

    if not compressors:
        print("No compressors detected (exe/ none and gzip/zstd not on PATH). Exiting.", file=sys.stderr)
        sys.exit(1)

    TMP_OUT_DIR.mkdir(exist_ok=True)
    results = []

    for label, meta in compressors.items():
        typ = meta["type"]
        factory = meta["factory"]
        print(f"\n=== Testing {label} (type={typ}) ===")
        if typ == "zstd":
            levels = zstd_levels
        else:
            levels = gzip_levels

        # --- Warm-up run (level 1) to avoid cold-start penalties ---
        try:
            warm_level = 1
            # choose extension
            if typ == "zstd" or label.lower().startswith("zstd"):
                warm_out = TMP_OUT_DIR / f"{TARBALL.name}.{label}.warmup.zst"
            else:
                warm_out = TMP_OUT_DIR / f"{TARBALL.name}.{label}.warmup.gz"
    
            warm_cmd = factory(warm_level, TARBALL, warm_out)
            print(f"[WARM-UP] Running: {' '.join(str(x) for x in warm_cmd)} > {warm_out}")
            _ = run_and_capture(warm_cmd, warm_out)
        except Exception as e:
            print(f"[WARN] Warm-up for {label} failed: {e}")
        finally:
            safe_unlink(warm_out)
        # --- End warm-up ---


        for level in levels:
            # choose extension
            if typ == "zstd" or label.lower().startswith("zstd"):
                outname = TMP_OUT_DIR / f"{TARBALL.name}.{label}.l{level}.zst"
            else:
                outname = TMP_OUT_DIR / f"{TARBALL.name}.{label}.l{level}.gz"

            cmd = factory(level, TARBALL, outname)
            print(f"Running: {' '.join(str(x) for x in cmd)} > {outname}")
            try:
                elapsed = run_and_capture(cmd, outname)
            except Exception as e:
                print(f"[ERROR] compressor {label} level {level} failed: {e}", file=sys.stderr)
                safe_unlink(outname)
                continue

            compressed_size = outname.stat().st_size
            mb_s = original_mb / elapsed if elapsed > 0 else 0.0
            percent = compressed_size / original_size * 100.0
            print(f"Level {level}: {elapsed:.3f}s  {mb_s:.1f} MB/s  {compressed_size} bytes ({percent:.2f}%)")

            results.append({
                "method": label,
                "level": int(level),
                "percent": round(percent, 2),
                "mb_s": round(mb_s, 2),
                "seconds": round(elapsed, 3),
                "compressed_bytes": int(compressed_size),
                "original_bytes": int(original_size)
            })

            # delete compressed output immediately
            safe_unlink(outname)

    # write TSV
    tsv_path = Path(f"{args.out}.tsv")
    with open(tsv_path, "w", newline="") as tf:
        writer = csv.writer(tf, delimiter="\t")
        writer.writerow(["method", "level", "percent", "mb_s", "seconds", "compressed_bytes", "original_bytes"])
        for r in results:
            writer.writerow([r["method"], r["level"], r["percent"], r["mb_s"], r["seconds"], r["compressed_bytes"], r["original_bytes"]])

    print(f"\nWrote {len(results)} rows to {tsv_path}")

if __name__ == "__main__":
    main()
