# pigz-bench

## Introduction

These simple scripts benchmark different zlib compression libraries for the [pigz](https://zlib.net/pigz/) parallel compressor. Parallel compression can use multiple cores available with modern computers to rapidly compress data. This technique can be combined with the [CloudFlare zlib](https://github.com/cloudflare/zlib) which accelerates compression using other features of modern hardware. Here, I have adapted the script to evaluate .gz compression of [NIfTI](https://nifti.nimh.nih.gov/) format brain images. It is common for tools like [AFNI](https://afni.nimh.nih.gov/) and [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki) to save NIfTI images using gzip compression (.nii.gz files).  Modern MRI methods such as multi-band yield huge datasets, so considerable [time](https://github.com/rordenlab/niimath) spent compressing these images.   

The  graph below shows the performance of pigz versus the default single-threaded pigz, so that '1' indicates equivalent performance. Performance is shown for 3 compression levels: fast (3, baseline 35 seconds), default (6, 50s) and slow (9, 183s). The horizontal axis shows the number of threads devoted to compression. At lower compression levels (1), all tools are relatively fast, with reading and writing from disk being the rate limiting factor. At higher compression levels the combination of multiple threads and CloudFlare enhancements dramatically accelerate the performance relative to the default gzip. The test system was a 24-core (48 thread) Intel Xeon Platinum 8260:

![alt tag](https://github.com/neurolabusc/pigz-bench/blob/master/pigz.png)

The next graph shows each tool using its preferred number of threads on a 4-core (8 thread) computer to compress the popular [Silesia corpus](http://sun.aei.polsl.pl/~sdeor/index.php?page=silesia). All versions of pigz outperform the system's single threaded gzip. One can see that the [modern zstd](https://facebook.github.io/zstd/) format dominates the older and simpler gzip. gzip has been widely adopted in many fields (for example in brain imaging it is used for [NIfTI](https://nifti.nimh.nih.gov), [NRRD](http://teem.sourceforge.net/nrrd/format.html) and [AFNI](https://afni.nimh.nih.gov/pub/dist/doc/program_help/README.compression.html)). The simplicity of the gzip format means it is easy for developers to include support in their tools. Therefore, gzip plays an important niche in the community. However, modern formats that were designed for modern hardware and leveraging new techniques have inherent benefits.

![alt tag](https://github.com/neurolabusc/pigz-bench/blob/master/speed_size.png)

The script `5decompress.sh` allows us to compare speed of decompression. Decompression is faster than compression. However, gzip decompression can not leverage multiple threads, and is generally slower than [modern compression formats](https://facebook.github.io/zstd/). In this test, all gz tools are decompressing that data. In contrast, bzip2 and ztd are decompressing data that was compressed to a smaller size. The speen in megabytes per second is calculated based on the decompressed size. It is typical for more compact compression to be use more complicated algorithms, so these comparing between formats is challenging. Regardless, among gz tools, zlib-ng shows superior decompression performance: 

| Speed (mb/s)  | pigz-CF  | pigz-ng  | pigz-Sys |   gzip   |  pbzip2  |  pbzip2  |
| ------------- | -------- | -------- | -------- | -------- | -------- | -------- |
| Decompression |     278  |     300  |     274  |     244  |     122  |     236  |

## Running the benchmark

Run the benchmark with a command like the following:

```
1compile.sh
2test.sh 
5decompress.sh
```

## The scripts

1. `1compile.sh` will download and build copies of pigz using different zlib variants (system, CloudFlare, ng). It also downloads sample images to test compression, specifically the [sample MRI scans](https://github.com/neurolabusc/zlib-bench) which are copied to the folder `corpus`. You **must** run this script once first, before the other scripts. All the other scripts can be run independently of each other. 
2. `2test.sh` compares the speed of the different versions of pigz as well as the system's single threaded gzip. You can replace the files in the `corpus` folder with ones more representative of your dataset.
3. `3slowtest.sh` downloads the [Silesia corpus](http://sun.aei.polsl.pl/~sdeor/index.php?page=silesia) and tests the compression speed. This corpus is popular: [benchmark 1](https://community.centminmod.com/threads/compression-comparison-benchmarks-zstd-vs-brotli-vs-pigz-vs-bzip2-vs-xz-etc.12764/), [benchmark 2](https://facebook.github.io/zstd/), [benchmark 3](https://github.com/valyala/gozstd/tree/master/zstd/contrib/pzstd).
4. `4verify.sh` tests the compression and decompression of each method, ensuring that they are able to store data without loss.
5. `5decompress.sh` evaluates the decompression speed. In general, the gzip format is slow to compress but fast to decompress (particularly compared to formats developed at the same time). However, gzip decompression is slow relative to the modern [zstd](https://facebook.github.io/zstd/). Further, while gzip compression can benefit from parallel processing, decompression does not. An important feature of this script is that each variant of zlib contributes compressed files to the testing corpus, and then each tool is tested on this full corpus. This ensures we are [comparing similar tasks](https://github.com/zlib-ng/zlib-ng/issues/326), as some zlib compression methods might generate smaller files at the cost of creating files that are slower to decompress.
6. `6speed_size.sh` compares different variants of pigz to gzip, zstd and bzip2 for compressing the [Silesia corpus](http://sun.aei.polsl.pl/~sdeor/index.php?page=silesia). Each tool is tested at different compression levels, but always using the preferred number of threads.

## Alternatives

 - Python users may want to examine [mgzip](https://pypi.org/project/mgzip/). Like pigz, mgzip can compress files to gz format in parallel. However, it can also decompress files created with mgzip in parallel. The gz files created by mgzip are completely valid gzip files, so they can be decompressed by any gzip compatible tool. However, these files require a tiny bit more disk space which allows parallel blocked decompression (as long as you use mgzip to do the decompression). For optimal performance, one should set a `blocksize` that correspnds to the number of threads for compression. This repository includes the `test_mgzip.py` script to evaluate this tool.
 - Python users can use [indexed-gzip](https://pypi.org/project/indexed-gzip/) to generate an index file for any gzip file. This index file accelerates random access to a gzip file.
 
 

