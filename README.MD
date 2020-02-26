# pigz-bench

## Introduction

This is a simple script to benchmark different zlib compression libraries for the [pigz](https://zlib.net/pigz/) parallel compressor. Parallel compression can use multiple cores available with modern computers to rapidly compress data. This technique can be combined with the [CloudFlare zlib](https://github.com/cloudflare/zlib) which accelerates compression using other features of modern hardware. Here, I have adapted the script to evaluate .gz compression of [NIfTI](https://nifti.nimh.nih.gov/) format brain images. It is common for tools like [AFNI](https://afni.nimh.nih.gov/) and [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki) to save NIfTI images using gzip compression (.nii.gz files).  Modern MRI methods such as multi-band yield huge datasets, so considerable [time](https://github.com/rordenlab/niimath) spent compressing these images.   

The  graph below shows the performance of pigz versus the default single-threaded pigz, so that '1' indicates equivalent performance. Performance is shown for 3 compression levels: fast (3, baseline 35 seconds), default (6, 50s) and slow (9, 183s).The horizontal axis shows the number of threads devoted to compression. At lower compression levels (1), all tools are relatively fast, with reading and writing from disk being the rate limiting factor. At higher compression levels the combination of multiple threads and CloudFlare enhancements dramatically accelerate the performance relative to the default gzip. The test system was a 24-core (48 thread) Intel Xeon Platinum 8260:

![alt tag](https://github.com/neurolabusc/pigz-bench/blob/master/pigz.png)

The zlib-ng performance falls between the system pigz and the CloudFlare pigz. The zlib-ng is currently focusing on a robust solution that can replace the classic baseline zlib. On the other hand, the CloudFlare zlib aggressively optimizes performance on modern x86-64 computers. However, this dataset does provide a clear example of how these tools perform differently.

## Running the benchmark

Run the benchmark with a command like the following:

```
1compile.sh
2test.sh 
```

The script 1compile will download and build copies of pigz using the default (system) zlib as well as a version of pigz using the accelerated CloudFlare zlib. It also downloads sample images to test compression, specifically the [sample MRI scans](https://github.com/neurolabusc/zlib-bench) which are copied to the folder `corpus`. 

The script `2test.sh` compares the speed of the different versions of pigz as well as the system's single threaded gzip. You can replace the files in the corpus folder with ones more representative of your dataset.

