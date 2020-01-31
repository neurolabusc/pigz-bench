# pigz-bench


## Introduction

This is a simple script to benchmark different zlib compression libraries for the [pigz](https://zlib.net/pigz/) parallel compressor. Parallel compression can use multiple cores available with modern computers to rapidly compress data. This technique can be combined with the [CloudFlare zlib](https://github.com/cloudflare/zlib) which accelerates compression using other features of modern hardware. Here, I have adapted the script to evaluate .gz compression of [NIfTI](https://nifti.nimh.nih.gov/) format brain images. It is common for tools like [AFNI](https://afni.nimh.nih.gov/) and [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki) to save NIfTI images using gzip compression (.nii.gz files).  Modern MRI methods such as multi-band yield huge datasets, so considerable [time](https://github.com/rordenlab/niimath) spent compressing these images.   

The  graph below shows the performance of pigz versus the default single-threaded gzip, so that '1' indicates equivalent performance. The horizontal axis shows the number of threads devoted to compression. At lower compression levels (1), all tools are relatively fast, with reading and writing from disk being the rate limiting factor. At higher compression levels the combination of multiple threads and CloudFlare enhancements dramatically accelerate the performance relative to the default gzip.
![alt tag](https://github.com/neurolabusc/pigz-bench/blob/master/pigz.png)

Here is the performance for a modern desktop with a 6 core (12 thread) CPU (Ubuntu 18.04, gcc 7.4, Intel i7 8700K):

| Compressor        |      -3       |      -6       |      -9       |
|-------------------|--------------:|--------------:|--------------:|
| gzip              | 31.2s (100%)  |  54.2s (100%) | 141.8s (100%) |
| pigz (system)     |  6.5s (21%)   |   8.9s (17%)  |  18.5s (13%)  |
| pigz (CloudFlare) |  4.9s (16%)   |   5.9s (11%)  |   7.5s (5%)   |




It is worth noting that [zlib-ng](https://github.com/zlib-ng/zlib-ng/issues/326) is currently focusing on a robust solution that can replace the classic baseline zlib. On the other hand, the CloudFlare zlib aggressively optimizes performance on modern x86-64 computers. However, this dataset does provide a clear example of how these tools perform differently.

## Running the benchmark

Run the benchmark with a command like the following:

```
1compile.sh
2test.sh 
```

The script 1compile will download and build copies of pigz using the default (system) zlib as well as a version of pigz using the accelerated CloudFlare zlib. It also downloads sample images to test compression, specifically the [sample MRI scans](https://github.com/neurolabusc/zlib-bench) which are copied to the folder `corpus`. 

The script `2test.sh` compares the speed of the different versions of pigz as well as the system's single threaded gzip. You can replace the files in the corpus folder with ones more representative of your dataset.

