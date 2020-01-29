# zlib-bench


## Introduction

This is a simple script by [Juho Snellman](https://github.com/jsnell/zlib-bench) to benchmark different zlib compression libraries.  Here, I have adapted the script to evaluate .gz compression of [NIfTI](https://nifti.nimh.nih.gov/) format brain images. It is common for tools like [AFNI](https://afni.nimh.nih.gov/) and [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki) to save NIfTI images using gzip compression (.nii.gz files).  Modern MRI methods such as multi-band yield huge datasets, so considerable [time](https://github.com/rordenlab/niimath) spent compressing these images.  Parallel compression (using [pigz](https://github.com/madler/pigz)) and accelerated zlib compression libraries like [CloudFlare zlib](https://github.com/cloudflare/zlib) and [zlib-ng](https://github.com/zlib-ng/zlib-ng) can have a dramatic benefit.

The results below are for the default (6) and extreme (9) compression levels, and each algorithm creates similarly sized output. Note that at the lowest compression levels (1), the zlib-ng creates larger files than the other methods but is dramatically faster.

Here we evaluate conversion of [ASL](https://osf.io/td4bx/wiki/home/) images. These files can be viewed with [MRIcroGL](https://github.com/rordenlab/MRIcroGL12/releases). The file asl16 is the raw 16-bit integer data from the scanner, which shows a low of high frequency noise throughout the image. The image asl32 has had all voxels outside the brain set to zero, has been blurred, and is saved as 32-bit floating point data, similar to post-processed NIfTI images. Since all the voxels outside the brain are zero in this image, the compression can leverage the redundancy to dramatically reduce file size. Note that while both CloudFlare and zlib-ng outperform the baseline library, the CloudFlare library is particularly fast for the scalp-stripped image.


Here is the performance for a modern MacOS laptop (MacOS 10.14.6 clang 11, Intel i5-8259U):

| Image        |    Baseline   |  CloudFlare   |   zlib-ng     |
|--------------|--------------:|--------------:|--------------:|
| asl16.nii -6 | 15.0s (100%)  |  7.7s (52%)   |  8.3s (55%)   |
| asl32.nii -6 | 6.4 (100%)    |  **4.4s (69%)**   |  5.8s (90%)   |
| asl16.nii -9 | 45.6s (100%)  |  11.3s (25%)   |  42.9s (94%)   |
| asl32.nii -9 | 18.3 (100%)    |  **7.7s (42%)**   |  9.1s (50%)   |


Here is the performance for a modern desktop (Ubuntu 19.10, gcc 9.2.1, Ryzen 3900X):


| Image        |    Baseline   |  CloudFlare   |   zlib-ng     |
|--------------|--------------:|--------------:|--------------:|
| asl16.nii -6 | 12.0s (100%)  |  6.3s (52%)   |  6.5s (54%)   |
| asl32.nii -6 | 6.5 (100%)    |  **3.6s (56%)**   |  5.0s (77%)   |
| asl16.nii -9 | 34.6s (100%)  |  10.11s (29%)   |  30.2s (87%)   |
| asl32.nii -9 | 10.5 (100%)    |  **6.4s (61%)**   |  7.5s (72%)   |

Here is the performance for old desktop (Ubuntu 14.04, gcc 4.8.4 Intel X5670):

| Image        |    Baseline   |  CloudFlare   |   zlib-ng     |
|--------------|--------------:|--------------:|--------------:|
| asl16.nii -6 | 18.1s (100%)  |  9.3s (52%)   |  15.6s (81%)   |
| asl32.nii -6 | 10.5 (100%)    |  **6.2s (60%)**   |  10.1s (97%)   |
| asl16.nii -9 | 50.1s (100%)  |  14.2s (28%)   |  **73.0s (146%)**   |
| asl32.nii -9 | 15.4 (100%)    |  **10.8s (70%)**   |  **20.5s (133%)**   |

It is worth noting that [zlib-ng](https://github.com/zlib-ng/zlib-ng/issues/326) is currently focusing on a robust solution that can replace the classic baseline zlib. On the other hand, the CloudFlare zlib aggressively optimizes performance on modern x86-64 computers. However, this dataset does provide a clear example of how these tools perform differently.

## Running the benchmark

Run the benchmark with a command like the following:

```
perl bench.pl --output-format=json --output-file=results.json
```

This will store the results in a json file for later analysis.


## Pretty-print the results

To pretty-print the results of an earlier run stored in a json file, use the --read-json flag.

```
perl bench.pl --read-json=results.json
```

## Changing which versions are tested against

To change the versions which are tested against, you need to edit the `@versions` variable in the source code (either the git repository urls or the version hashes). Note that if you change the definition of existing entries under versions (or if you e.g. upgrade the compiler), you’ll probably want to run with the `--recompile` flag the next time.

## Adding new input files to the benchmark

Any files starting with a small letter in the corpus/ directory will be used as inputs, each one creating a new benchmark family (decompression, compression at each specified compression level). The name of the file is used as the benchmark id in reports.

## Full options

```
--help                 Print a help message
--compress-iters=...   Number of times each file is compressed in one
                       benchmark run
--compress-levels=...  Comma-separated list of compression levels to use
--decompress-iters=... Number of times each file is compressed in one
                       benchmark run
--output-file=...      File (- for stdout) where results are printed to
--output-format=...    Format to output results in (pretty, json)
--read-json=...        Don't run benchmarks, but read results from this file
--recompile            If passed, recompile all zlib versions before test
--runs=...             Number of runs for each benchmark
--quiet                Don't print progress reports to STDERR
```

## Alternatives

There are modern compression methods like [zstd](http://richg42.blogspot.com/2016/08/rads-ground-breaking-lossless.html) that outperform the classic GZ format. Furter, most compression tools are tuned for 8-bit data, and methods like [BLOSC](https://blosc.org/posts/zstd-has-just-landed-in-blosc/) can aid the 16, 32 and 64 bit datatypes common in science. However, gz is simple and ubiquitous, and is the accepted compression format for NIfTI images.

