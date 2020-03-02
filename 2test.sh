#!/bin/bash
# ./2test.sh                #test performance for data in default folder "corpus"
# ./2test.sh SilesiaCorpus  #test performance for data in folder "SilesiaCorpus" 

if [ -z ${basedir:-} ]; then
    basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

if [ $# -lt 1 ]; then
	indir=${basedir}/corpus
else
	indir=$1
fi

#pct = % reduction, e.g. 10.0 = .gz is 10% of uncompressed size
pct=0
#reps - number of times each file is compressed
reps=1
#ms= milliseconds to compress all files
ms=0
#mbs= megabytes per sec
mbs=0
#bytesPerMegabyte: you could also choose 1024x1024
bytesPerMegabyte=1000000


setPct() {
	#take advantage that bash scripts do not scope variables
	#must use nested script as return values are only 0..255
	sum=0
	sumgz=0
	for fx in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
		if [[ "$OSTYPE" == "darwin"* ]]; then
			sz=$(stat -f%z "$fx")
		else
			sz=$(stat -c%s "$fx")
		fi
		if [ ! "${fx##*.}" = "gz" ]; then
			sum=$(($sum + $sz))
		else
			sumgz=$(($sumgz + $sz))	
		fi
	done
	pct=$(bc <<<"scale=3;100.0*$sumgz/$sum")
	#1000 ms per second
	scale=$((reps * 1000 * $sum / $bytesPerMegabyte))
	mbs=$(($scale / $ms))
}

#### no need to edit subsequent lines
if [[ "$OSTYPE" == "darwin"* ]]; then
	echo Make sure to "'"brew install coreutils"'"
	shopt -s expand_aliases
	alias date='gdate'
fi
#folder paths
exedir=${basedir}/exe


#./batch.sh
echo -e "Method\tLevel\tThreads\tms\t%\tmb/sec"
for file in $exedir/*; do
	for lvl in {3,6,9}; do
		for t in {1,2,4,0}; do	
			cmd="./_test.sh $lvl $file $t $indir $reps"
			#echo "Running command: $cmd"
			startTime=$(date +%s%3N)
			$cmd
			ms=$(($(date +%s%3N)-$startTime))
			setPct
			filename=$(basename -- "$file")
			echo -e "$filename\t$lvl\t$t\t$ms\t$pct\t$mbs"
		done
	done
done

#compare vs system gzip
for lvl in {3,6,9}; do
	cmd="./_test.sh $lvl gzip 0 $indir $reps"
	#echo "Running command: $cmd"
	startTime=$(date +%s%3N)
	$cmd
	ms=$(($(date +%s%3N)-$startTime))
	setPct
	echo -e "gzip\t$lvl\t1\t$ms\t$pct\t$mbs"
done
#report bytes


