#!/bin/bash
# ./5decompress.sh                #test performance for data in default folder "corpus"
# ./5decompress.sh SilesiaCorpus  #test performance for data in folder "SilesiaCorpus" 

if [ -z ${basedir:-} ]; then
    basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

if [ $# -lt 1 ]; then
	indir=${basedir}/corpus
else
	indir=$1
fi

#### no need to edit subsequent lines
if [[ "$OSTYPE" == "darwin"* ]]; then
	echo Make sure to "'"brew install coreutils"'"
	shopt -s expand_aliases
	alias date='gdate'
fi
#folder paths
exedir=${basedir}/exe
#create temporary directory with compressed files created by each tool
outdir=${basedir}/tmp
mkdir -p $outdir
rm -rf $outdir/*
#total number of uncompressed bytes
bytes=0
for fx in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
	if [[ "$OSTYPE" == "darwin"* ]]; then
		sz=$(stat -f%z "$fx")
	else
		sz=$(stat -c%s "$fx")
	fi
	if [ ! "${fx##*.}" = "gz" ]; then
		bytes=$(($bytes + $sz))
	fi
done

#create files with each exe and different compression levels
nCopy=0
for exenam in $exedir/*; do
	exe=${exenam##*/}
	for lvl in {3,6,9}; do
		nCopy=$(($nCopy + 1))
		for file in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
			if [ ! "${file##*.}" = "gz" ]; then
				outnam=$outdir/$exe$lvl${file##*/}.gz
				cmd="$exenam -f -k -$lvl $file"
				#echo "Running command: '$cmd'"
				$cmd
				cmd="cp ${file}.gz $outnam"
				$cmd
			fi
		done
	done
done

#bytesPerMegabyte: you could also choose 1024x1024
bytesPerMegabyte=1000000
#1000 ms per second
scale=$(($nCopy * 1000 * $bytes / $bytesPerMegabyte))

#test each tool on all methods
echo -e "DecompressMethod\tms\tmb/sec"
#create files with each exe and different compression levels
for exenam in $exedir/*; do
	filename=$(basename -- "$exenam")
	cmd="./_decompress.sh $exenam $outdir"
	#echo "Running command: $cmd"
	startTime=$(date +%s%3N)
	$cmd
	ms=$(($(date +%s%3N)-$startTime))
	mbs=$(($scale / $ms))
	echo -e "$filename\t$ms\t$mbs"
done
exenam=gzip
filename=$(basename -- "$exenam")
cmd="./_decompress.sh $exenam $outdir"
startTime=$(date +%s%3N)
$cmd
ms=$(($(date +%s%3N)-$startTime))
mbs=$(($scale / $ms))
echo -e "$filename\t$ms\t$mbs"

#cleanup - remove temporary folder
rm -rf $outdir

#optional: test zstd speed
./_decompress_bz2.sh $indir
#optional: test zstd speed
./_decompress_zstd.sh $indir
exit 0

