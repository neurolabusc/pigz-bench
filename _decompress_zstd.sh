#!/bin/bash
# ./_decompress_zstd.sh                #test performance for data in default folder "corpus"
# ./_decompress_zstd.sh SilesiaCorpus  #test performance for data in folder "SilesiaCorpus" 
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

outdir=${basedir}/tmp
mkdir -p $outdir

exenam=zstd
rm -rf $outdir/*
nCopy=0
#for lvl in {1,3,6,9,11,13,15,17,19}; do
for lvl in {1,3,6,9,11,13}; do
	nCopy=$(($nCopy + 1))
	for file in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
		if [ ! "${file##*.}" = "gz" ]; then
			outnam=$outdir/$lvl${file##*/}.zst
			cmd="$exenam -T0 -q -f -k -$lvl $file"
			#echo "Running command: '$cmd'"
			$cmd
			cmd="cp ${file}.zst $outnam"
			#echo " '$cmd'"
			$cmd
			rm ${file}.zst
			#exit 1
		fi
	done
done

#bytesPerMegabyte: you could also choose 1024x1024
bytesPerMegabyte=1000000
#1000 ms per second
scale=$(($nCopy * 1000 * $bytes / $bytesPerMegabyte))


filename=$(basename -- "$exenam")
echo -e "DecompressMethod\tms\tmb/sec"
startTime=$(date +%s%3N)
for file in $(find ${outdir}/* -maxdepth 1 -type f); do # only regular file in the current dir
	if [ "${file##*.}" = "zst" ]; then
		cmd="$exenam -T0 -q -f -k -d $file"
		#echo "Running command: '$cmd'"
		$cmd
	fi
done
ms=$(($(date +%s%3N)-$startTime))
mbs=$(($scale / $ms))
echo -e "$filename\t$ms\t$mbs"
#cleanup - remove temporary folder
rm -rf $outdir
exit 0
