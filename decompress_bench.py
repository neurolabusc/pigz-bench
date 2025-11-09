#!/usr/bin/env python3
"""
decompress_bench.py

Per-file compression + decompression benchmark.

- Compress every file in DATASET_DIR for each compressor (local exe in exe/, system gzip, optional zstd)
  producing: <inputfile>.<method>.l<level>.gz  (or .zst for zstd)
- After all compressors/levels have produced outputs, for each decompressor:
    * For each compressed file, run decompression nruns times
    * Discard first run (warm-up), average the remaining nruns-1 runs for that file
    * Sum averaged times across files to get total_time
    * Compute MB/s = (total_original_bytes / 1_000_000) / total_time
- Writes a TSV with columns: method\tmb_s and prints a Markdown table.

Usage:
    python3 decompress_bench.py
    python3 decompress_bench.py --exe-dir ./exe --levels 1 3 9 --zstd-levels 1 3 19 --nruns 5
"""
from pathlib import Path
import argparse
import csv
import subprocess
import shutil
import sys
import time
import os
import tempfile

# ---------- Config / defaults ----------
SCRIPT_DIR = Path(__file__).resolve().parent
EXE_DIR_DEFAULT = SCRIPT_DIR / "exe"
GIT_URL = "https://github.com/MiloszKrajewski/SilesiaCorpus"
DATASET_DIR = Path("SilesiaCorpus")
TMP_OUT_DIR = Path("tmp_compress_outputs")
DEFAULT_GZIP_LEVELS = [1, 3, 6, 7, 9]       # gzip / pigz levels
DEFAULT_ZSTD_LEVELS = [1, 3, 10, 19]        # zstd levels
OUT_TSV = SCRIPT_DIR / "decompress.tsv"
BYTES_PER_MB = 1_000_000                    # match shell style 1,000,000 bytes/MB

# ---------- Helpers ----------
def detect_local_exes(exe_dir: Path):
    comps = {}
    if not exe_dir.exists():
        return comps
    for p in sorted(exe_dir.iterdir()):
        if p.is_file() and os.access(str(p), os.X_OK):
            comps[p.name] = p
    return comps

def detect_system(name):
    return shutil.which(name)

def safe_unlink(p: Path):
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass

def run_cmd_get_elapsed(cmd, stdout_target=None):
    """Run command list, optionally redirect stdout to file-like or file path.
    Returns elapsed seconds and raises on non-zero exit."""
    # stdout_target can be a file object or path or None (will be inherited / suppressed)
    stdout_obj = None
    opened = False
    try:
        if stdout_target is None:
            stdout_obj = subprocess.DEVNULL
        elif isinstance(stdout_target, (str, Path)):
            stdout_obj = open(str(stdout_target), "wb")
            opened = True
        else:
            stdout_obj = stdout_target  # assume file-like

        start = time.monotonic()
        proc = subprocess.run(cmd, stdout=stdout_obj, stderr=subprocess.PIPE)
        end = time.monotonic()
        elapsed = end - start
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Command failed (rc={proc.returncode}): {stderr}")
        return elapsed
    finally:
        if opened and stdout_obj:
            stdout_obj.close()

# ---------- Compression functions ----------
def compress_file_gzip_like(label, path_to_exe, level, infile: Path, outpath: Path):
    """
    Compress a single infile using gzip-like tool into outpath.
    pigz variants all threads by default.
    """
    if label == "gzip":
        cmd = [str(path_to_exe), f"-{level}", "-c", str(infile)]
    else:
        # pigz-like
        cmd = [str(path_to_exe), f"-{level}", "-c", str(infile)]

    # run and write stdout to outpath
    with open(outpath, "wb") as of:
        start = time.monotonic()
        proc = subprocess.run(cmd, stdout=of, stderr=subprocess.PIPE)
        end = time.monotonic()
        elapsed = end - start
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Compression failed ({label} level {level} on {infile}): {stderr}")
    return elapsed

def compress_file_zstd(zstd_path, level, infile: Path, outpath: Path):
    cmd = [str(zstd_path), f"-{level}", "-c", str(infile)]
    with open(outpath, "wb") as of:
        start = time.monotonic()
        proc = subprocess.run(cmd, stdout=of, stderr=subprocess.PIPE)
        end = time.monotonic()
        elapsed = end - start
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"zstd compression failed (level {level} on {infile}): {stderr}")
    return elapsed

# ---------- Decompression timing helpers ----------
def avg_time_last_runs(cmd, infile_desc, nruns=5, target="devnull", outdir=None):
    """
    Run cmd (list) nruns times capturing stdout as specified by target:
      - 'devnull' -> drop output to /dev/null
      - 'tmp'     -> write to a temp file under outdir (if provided) then delete
      - 'file'    -> write to a temp file under outdir and leave (or delete after)
    Return average of last nruns-1 runs (drop first warm-up).
    """
    times = []
    tmp_paths = []
    for i in range(nruns):
        if target == "devnull":
            stdout_target = subprocess.DEVNULL
            out_path = None
        else:
            outdir_path = Path(outdir) if outdir else Path(tempfile.gettempdir())
            outdir_path.mkdir(parents=True, exist_ok=True)
            fd, tname = tempfile.mkstemp(prefix=f"decomp-", suffix=".out", dir=str(outdir_path))
            stdout_target = os.fdopen(fd, "wb")
            out_path = Path(tname)
            tmp_paths.append(out_path)

        start = time.monotonic()
        proc = subprocess.run(cmd, stdout=stdout_target, stderr=subprocess.PIPE)
        end = time.monotonic()
        elapsed = end - start

        # close if we opened a file
        if stdout_target is not subprocess.DEVNULL and hasattr(stdout_target, "close"):
            try:
                stdout_target.close()
            except Exception:
                pass

        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace")
            # cleanup tmp files
            for p in tmp_paths:
                safe_unlink(p)
            raise RuntimeError(f"Decompression failed ({infile_desc}): {stderr}")

        times.append(elapsed)
        # remove temporary output file immediately (we're not keeping output)
        if out_path is not None:
            safe_unlink(out_path)

    if len(times) <= 1:
        return times[0] if times else 0.0
    # average last nruns-1 runs
    avg = sum(times[1:]) / (len(times) - 1)
    return avg

# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="Per-file compression + decompression benchmark")
    parser.add_argument("--exe-dir", default=str(EXE_DIR_DEFAULT), help="Directory with pigz variants (executables)")
    parser.add_argument("--levels", nargs="+", type=int, default=DEFAULT_GZIP_LEVELS,
                        help="gzip/pigz levels to compress (1..9)")
    parser.add_argument("--zstd-levels", nargs="+", type=int, default=DEFAULT_ZSTD_LEVELS,
                        help="zstd levels to compress (1..19)")
    parser.add_argument("--nruns", type=int, default=5, help="Number of decompression runs per file (first is warm-up)")
    parser.add_argument("--decomp-target", choices=["devnull", "tmp", "file"], default="tmp",
                        help="Where decompressed output is written during timing (devnull=fastest, tmp=tmpfs recommended)")
    parser.add_argument("--out", default=str(OUT_TSV), help="Output TSV path")
    parser.add_argument("--skip-clone", action="store_true", help="Skip cloning dataset")
    parser.add_argument("--recreate-files", action="store_true", help="Recreate compressed files even if present")
    args = parser.parse_args()

    exe_dir = Path(args.exe_dir)

    # validate ranges
    for l in args.levels:
        if l < 1 or l > 9:
            print(f"[ERROR] gzip/pigz level {l} out of range 1..9", file=sys.stderr)
            sys.exit(2)
    for l in args.zstd_levels:
        if l < 1 or l > 19:
            print(f"[ERROR] zstd level {l} out of range 1..19", file=sys.stderr)
            sys.exit(2)
    if args.nruns < 2:
        print("[ERROR] nruns must be >= 2 (we drop the first run as warm-up)", file=sys.stderr)
        sys.exit(2)

    # ensure dataset available
    if not args.skip_clone:
        # simple clone if missing (non-robust but fine for this script)
        if not DATASET_DIR.exists():
            print(f"Cloning {GIT_URL} ...")
            subprocess.run(["git", "clone", GIT_URL], check=True)
    else:
        print("Skipping clone as requested.")

    # collect corpus files (regular files only)
    if not DATASET_DIR.exists():
        print(f"[ERROR] Dataset directory {DATASET_DIR} not found", file=sys.stderr)
        sys.exit(1)

    corpus_files = [p for p in sorted(DATASET_DIR.iterdir()) if p.is_file()]
    if not corpus_files:
        print(f"[ERROR] No files found in {DATASET_DIR}", file=sys.stderr)
        sys.exit(1)

    # prepare output dir
    TMP_OUT_DIR.mkdir(exist_ok=True)

    # detect compressors
    local_exes = detect_local_exes(exe_dir)
    gzip_path = detect_system("gzip")
    zstd_path = detect_system("zstd")

    # build compressor maps
    gzip_like = {}
    if gzip_path:
        gzip_like["gzip"] = Path(gzip_path)
    for k, v in local_exes.items():
        gzip_like[k] = v

    if not gzip_like:
        print("[ERROR] No gzip-like compressors found (gzip not on PATH and exe/ empty).", file=sys.stderr)
        sys.exit(1)

    print("Compressing each corpus file with each gzip-like compressor and level...")
    compressed_files = []  # list of tuples (method, level, in_path, out_path)
    # compress per file
    for infile in corpus_files:
        for label, pth in gzip_like.items():
            for level in args.levels:
                outname = TMP_OUT_DIR / f"{infile.name}.{label}.l{level}.gz"
                if outname.exists() and not args.recreate_files:
                    print(f"Skipping existing {outname}")
                else:
                    print(f"Compressing {infile.name} -> {outname}  ({label} -{level})")
                    try:
                        compress_file_gzip_like(label, pth, level, infile, outname)
                    except Exception as e:
                        print(f"[ERROR] compression failed for {label} on {infile}: {e}", file=sys.stderr)
                        safe_unlink(outname)
                        continue
                compressed_files.append((label, level, infile, outname))

    # zstd compressions (if zstd available)
    zst_files = []
    if zstd_path:
        for infile in corpus_files:
            for level in args.zstd_levels:
                outname = TMP_OUT_DIR / f"{infile.name}.zstd.l{level}.zst"
                if outname.exists() and not args.recreate_files:
                    print(f"Skipping existing {outname}")
                else:
                    print(f"Compressing {infile.name} -> {outname}  (zstd -{level})")
                    try:
                        compress_file_zstd(zstd_path, level, infile, outname)
                    except Exception as e:
                        print(f"[ERROR] zstd compression failed for {infile} level {level}: {e}", file=sys.stderr)
                        safe_unlink(outname)
                        continue
                zst_files.append(("zstd", level, infile, outname))

    # Build the list of compressed file groups to test decompression on:
    # For gzip-like methods we will test across the corresponding .gz files
    # We'll group by method so we can test each decompressor against all files created by all compressors.
    # But per your requirement: "For gzip variants we want to ensure they decompress all the other variants compressed files"
    # we'll generate the complete list of produced compressed files and let each decompressor attempt to decompress everything.
    all_compressed = []
    all_compressed.extend(compressed_files)
    all_compressed.extend(zst_files)

    if not all_compressed:
        print("[ERROR] No compressed files produced; aborting.", file=sys.stderr)
        sys.exit(1)

    # total original bytes for MB/s calculation = sum of sizes of unique input files we will decompress for each compressed file
    # For per-file approach total_original_bytes = sum(original_size for each compressed file) == sum(original_size * number_of_compressed_files_from_all_methods)
    # But we want MB/s where total bytes decompressed equals the sum of original file sizes for each compressed file decompressed.
    # We'll compute per-decompressor total bytes as sum(infile.stat().st_size for each compressed file it processes).
    print("\nStarting decompression measurements (per decompressor) ...")
    results = []  # list of (method, mb_s)

    # Build list of decompressor methods: gzip-like (local + system) and zstd (if present)
    decompress_methods = {}
    # gzip-like decompressors are the same set as gzip_like
    for label, pth in gzip_like.items():
        decompress_methods[label] = {"type": "gzip-like", "path": pth}
    if zstd_path:
        decompress_methods["zstd"] = {"type": "zstd", "path": Path(zstd_path)}

    # For each decompressor, attempt to decompress ALL compressed files produced above, time them (nruns per file)
    for method, meta in decompress_methods.items():
        print(f"\n=== Testing decompressor: {method} (type={meta['type']}) ===")
        total_time = 0.0
        total_bytes = 0
        success = True
        for (src_label, level, infile, comp_path) in all_compressed:
            # choose command depending on method and file type
            # ensure method attempts to decompress files regardless of which compressor produced them
            if comp_path.suffix == ".zst":
                # file is zstd compressed; only zstd should be able to decompress it
                if method != "zstd":
                    # skip: gzip-like decompressors can't handle .zst
                    continue
                cmd = [str(meta["path"]), "-d", "-c", str(comp_path)]
                infile_desc = f"{comp_path.name} (zstd)"
            else:
                # .gz file - method may be gzip-like or zstd (zstd won't be used here)
                if meta["type"] != "gzip-like":
                    # skip if method is not gzip-like (only gzip-like can handle .gz)
                    continue
                # pigz variants
                if method == "gzip":
                    cmd = [str(meta["path"]), "-d", "-c", str(comp_path)]
                else:
                    cmd = [str(meta["path"]), "-d", "-c", str(comp_path)]
                infile_desc = f"{comp_path.name} (gz)"

            # Perform nruns decompressions for this compressed file, take average of last nruns-1
            try:
                avg_sec = avg_time_last_runs(cmd, infile_desc, nruns=args.nruns,
                                             target=args.decomp_target if args.decomp_target != "devnull" else "devnull",
                                             outdir=None)
            except Exception as e:
                print(f"[ERROR] {method} failed to decompress {comp_path}: {e}", file=sys.stderr)
                success = False
                break

            # accumulate
            total_time += avg_sec
            try:
                original_sz = infile.stat().st_size
            except Exception:
                original_sz = 0
            total_bytes += original_sz

        if not success or total_time <= 0 or total_bytes == 0:
            print(f"[WARN] Skipping result for {method} due to errors or zero time/bytes.")
            continue

        total_mb = total_bytes / BYTES_PER_MB
        mb_s = total_mb / total_time if total_time > 0 else 0.0
        print(f"[RESULT] {method}: total_files={len([1 for _ in all_compressed if True])}, total_bytes={total_bytes}, total_time={total_time:.3f}s, mb_s={mb_s:.2f}")
        results.append((method, mb_s))

    # cleanup compressed files
    print("\nCleaning up compressed files...")
    for (_, _, _, p) in all_compressed:
        safe_unlink(p)

    # write TSV and print markdown
    print("\nWriting output TSV...")
    rows = [{"method": m, "mb_s": round(v, 2)} for m, v in results]
    if rows:
        with open(args.out, "w", newline="") as tf:
            writer = csv.writer(tf, delimiter="\t")
            writer.writerow(["method", "mb_s"])
            for r in rows:
                writer.writerow([r["method"], r["mb_s"]])
        print(f"Wrote {len(rows)} rows to {args.out}")

        print("\nMarkdown summary table:\n")
        print("| method | mb_s |")
        print("| ------- | -----:|")
        for r in rows:
            print(f"| {r['method']} | {r['mb_s']:.2f} |")
    else:
        print("[WARN] No results to write.", file=sys.stderr)

    print("Done.")

if __name__ == "__main__":
    main()
