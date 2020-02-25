#!/bin/bash -i
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
#create files with each exe and different compression levels
for exenam in $exedir/*; do
	exe=${exenam##*/}
	for lvl in {3,6}; do
		for file in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
			if [ ! "${file##*.}" = "gz" ]; then
				outnam=$outdir/$exe$lvl${file##*/}.gz
				cmd="$exenam -f -k -$lvl $file"
				#echo "Running command: '$cmd'"
				$cmd
				cmd="cp ${file}.gz $outnam"
				#echo " '$cmd'"
				$cmd
			fi
		done
	done
done

#test each tool on all methods
echo -e "DecompressMethod\tms"
#create files with each exe and different compression levels
for exenam in $exedir/*; do
	filename=$(basename -- "$exenam")
	cmd="./_decompress.sh $exenam $outdir"
	#echo "Running command: $cmd"
	startTime=$(date +%s%3N)
	$cmd
	echo -e "$filename\t$(($(date +%s%3N)-$startTime))"
done

exenam=gzip
filename=$(basename -- "$exenam")
cmd="./_decompress.sh $exenam $outdir"
startTime=$(date +%s%3N)
$cmd
echo -e "$filename\t$(($(date +%s%3N)-$startTime))"

#report bytes
./_sizenotgz.sh $outdir

#cleanup - remove temporary folder
rm -rf $outdir
