#!/usr/bin/env python3
"""
compile_pigz.py

Python translation of 1compile.sh:
  - clones neurolabusc/pigz
  - builds pigz with different ZLIB_IMPLEMENTATION values (Cloudflare, System, ng)
  - copies built pigz binaries to ./exe/
  - clones neurolabusc/zlib-bench, copies all .nii files into ./corpus/
  - cleans up temporary build directories

Equivalent to the original shell script. See original: :contentReference[oaicite:1]{index=1}
"""
from pathlib import Path
import subprocess
import shutil
import os
import sys
import argparse

def run(cmd, cwd=None, env=None, hide_output=False):
    print(f"> {' '.join(cmd)} (cwd={cwd})")
    subprocess.run(cmd, cwd=cwd, check=True, env=env)

def rm_rf(path: Path):
    if path.exists():
        if path.is_dir():
            print(f"Removing directory {path}")
            shutil.rmtree(path)
        else:
            print(f"Removing file {path}")
            path.unlink()

def ensure_dir(path: Path):
    if not path.exists():
        print(f"Creating directory {path}")
        path.mkdir(parents=True, exist_ok=True)

def copy_tree_find(src_root: Path, pattern: str, dest_dir: Path):
    """
    Recursively find files under src_root matching pattern (glob style)
    and copy them into dest_dir (flat copy).
    """
    print(f"Searching for files {pattern} under {src_root} to copy into {dest_dir}")
    found = list(src_root.rglob(pattern))
    for p in found:
        if p.is_file():
            print(f"  copying {p} -> {dest_dir}")
            shutil.copy2(p, dest_dir)
    print(f"Copied {len(found)} files matching {pattern}")

def build_and_copy_libdeflate(basedir: Path, exedir: Path, optimize: bool = False):
    """
    Clone libdeflate, build with CMake Release, and copy libdeflate-gzip -> exe/libdeflate (or .exe on Windows).
    """
    repo_dir = basedir / "libdeflate"
    build_dir = repo_dir / "build"
    # Remove existing clone to ensure fresh build
    rm_rf(repo_dir)

    print("Cloning libdeflate...")
    run(["git", "clone", "https://github.com/ebiggers/libdeflate.git"], cwd=str(basedir))

    # Ensure build dir exists
    if build_dir.exists():
        rm_rf(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Configure step: use Release and forward optional knobs similar to pigz script
    cmake_cmd = ["cmake", "-DCMAKE_BUILD_TYPE=Release", ".."]
    if optimize:
        # If your top-level CMake supports these options, enable them for libdeflate as well.
        # (These flags will be ignored if libdeflate CMakeLists.txt doesn't define them.)
        cmake_cmd.insert(1, "-DENABLE_LTO=ON")
        cmake_cmd.insert(1, "-DTUNE_NATIVE=ON")

    print(f"> Configuring libdeflate: {' '.join(cmake_cmd)} (cwd={build_dir})")
    run(cmake_cmd, cwd=str(build_dir))

    # Build step
    print("> Building libdeflate...")
    run(["cmake", "--build", str(build_dir), "--config", "Release"], cwd=str(repo_dir))

    # Program path: build/programs/libdeflate-gzip (or libdeflate-gzip.exe)
    prog_dir = build_dir / "programs"
    # Accept either exact name or platform-suffixed
    exe_suffix = ".exe" if os.name == "nt" else ""
    candidates = [
        prog_dir / f"libdeflate-gzip{exe_suffix}",
        prog_dir / f"libdeflate_gzip{exe_suffix}",
    ]
    found = None
    for c in candidates:
        if c.exists():
            found = c
            break
    # Fallback: try glob for anything starting with libdeflate-gzip
    if found is None and prog_dir.exists():
        for p in prog_dir.iterdir():
            if p.is_file() and p.name.startswith("libdeflate-gzip"):
                found = p
                break

    if not found:
        raise RuntimeError(f"Could not find built libdeflate-gzip executable in {prog_dir}")

    # Destination path: ./exe/libdeflate (preserve .exe on Windows)
    dest_name = "libdeflate.exe" if os.name == "nt" else "libdeflate"
    dest_path = exedir / dest_name
    ensure_dir(exedir)
    print(f"Copying {found} -> {dest_path}")
    shutil.copy2(str(found), str(dest_path))
    if os.name != "nt":
        dest_path.chmod(0o755)
    print("libdeflate installed to", dest_path)
    rm_rf(repo_dir)

def main():
    try:
        parser = argparse.ArgumentParser(description="Compile pigz variants")
        parser.add_argument("--optimize", action="store_true",
                            help="Enable TUNE_NATIVE and LTO")
        args = parser.parse_args()
        # honour an externally provided basedir if set (like the shell script)
        basedir_env = os.environ.get("basedir") or os.environ.get("BASEDIR")
        if basedir_env:
            basedir = Path(basedir_env).expanduser().resolve()
        else:
            basedir = Path(__file__).resolve().parent

        print(f"basedir = {basedir}")

        exedir = basedir / "exe"

        exeSys = exedir / "pigzSys"
        exeCF = exedir / "pigzCF"
        exeNG = exedir / "pigzNG"

        # remove previous artifacts
        rm_rf(basedir / "pigz")
        rm_rf(exedir)
        ensure_dir(exedir)

        # clone pigz repo
        print("Cloning pigz repo...")
        run(["git", "clone", "https://github.com/neurolabusc/pigz.git"], cwd=basedir)

        pigz_dir = basedir / "pigz"
        build_dir = pigz_dir / "build"

        # helper to build with a given ZLIB_IMPLEMENTATION value and copy bin/pigz
        def build_variant(zlib_impl: str, target_path: Path):
            # ensure build directory exists and is empty
            if build_dir.exists():
                print(f"Cleaning build directory {build_dir}")
                # remove contents but keep build_dir itself
                for child in build_dir.iterdir():
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
            else:
                build_dir.mkdir(parents=True)

            print(f"Configuring pigz with ZLIB_IMPLEMENTATION={zlib_impl}")
            # run cmake and make
            cmake_cmd = ["cmake", "-DCMAKE_BUILD_TYPE=Release",
                         f"-DZLIB_IMPLEMENTATION={zlib_impl}", ".."]
    
            # If --optimize is set, enable both TUNE_NATIVE and LTO
            if args.optimize:
                cmake_cmd.insert(1, "-DENABLE_LTO=ON")
                cmake_cmd.insert(1, "-DTUNE_NATIVE=ON")
    
            print(f"> Config command: {' '.join(cmake_cmd)} (cwd={build_dir})")
    
            # Run cmake and make
            run(cmake_cmd, cwd=str(build_dir))
            run(["make"], cwd=str(build_dir))
            # copy built binary
            bin_path = build_dir / "bin" / "pigz"
            if not bin_path.exists():
                raise RuntimeError(f"Expected built pigz binary not found at {bin_path}")
            print(f"Copying {bin_path} -> {target_path}")
            shutil.copy2(bin_path, target_path)
            # make executable (just in case)
            target_path.chmod(0o755)

        # build CloudFlare pigz
        print("Building CloudFlare pigz (pigzCF)...")
        build_variant("Cloudflare", exeCF)

        # build System pigz
        print("Building System pigz (pigzSys)...")
        build_variant("System", exeSys)

        # build zlib-ng pigz
        print("Building ng (pigzNG)...")
        build_variant("ng", exeNG)

        # optional: other implementations can be added similarly (Intel etc.)

        # cleanup pigz source tree
        print("Cleaning up pigz source directory...")
        rm_rf(pigz_dir)
        # libdeflate
        print("Building libdeflate and copying its gzip program to ./exe/")
        build_and_copy_libdeflate(basedir, exedir, optimize=args.optimize)
        print("Success: run 'compress_bench.py' and 'decompress_bench.py'")

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
