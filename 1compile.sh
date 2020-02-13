#!/bin/bash

# Fail if anything not planed to go wrong, goes wrong
set -eu

#basedir is folder with "Ref" and "In" subfolders.
# we assume it is the same same folder as the script
# however, this could be set explicitly, e.g.
#   basedir="/Users/rorden/dcm_qa" batch.sh
if [ -z ${basedir:-} ]; then
    basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi
indir=${basedir}/corpus
exedir=${basedir}/exe

exeSys=$exedir/pigzSys
exeCF=$exedir/pigzCF

#build different versions of pigz
rm -rf pigz
rm -rf $exedir
mkdir $exedir
git clone --branch windows https://github.com/neurolabusc/pigz.git

cd pigz; mkdir build && cd build
cmake -DZLIB_IMPLEMENTATION=Cloudflare ..
make
cp ./bin/pigz $exeCF
#make system pigz
rm -rf *
cmake -DZLIB_IMPLEMENTATION=System ..
make
cp ./bin/pigz $exeSys
#make zlib-ng pigz
exeNG=$exedir/pigzNG
rm -rf *
cmake -DZLIB_IMPLEMENTATION=ng ..
make
cp ./bin/pigz $exeNG
#make zlib-ng pigz
exeIntel=$exedir/pigzIntel
rm -rf *
cmake -DZLIB_IMPLEMENTATION=Intel ..
make
cp ./bin/pigz $exeIntel

cd $basedir
rm -rf pigz

rm -rf $indir
mkdir $indir
tmpdir=${basedir}/zlib-bench
rm -rf $tmpdir
git clone https://github.com/neurolabusc/zlib-bench.git
 find . -name \*.nii -exec cp {} $indir \;
rm -rf $tmpdir

echo "Success: run '2test.sh'"
exit 0





