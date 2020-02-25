#!/bin/bash
# ./4verify.sh                #verify lossless performance for "corpus"
# ./4verify.sh SilesiaCorpus  #verify lossless performance for "SilesiaCorpus" 

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


#./batch.sh
echo -e "Method\tLevel\tThreads\tms"
for file in $exedir/*; do
	for lvl in {1,2,3,4,5,6,7,8,9}; do
		for t in {1,2,4,8,12,16,24,32,48}; do		
			cmd="./_verify.sh $lvl $file $t $indir"
			#echo "Running command: $cmd"
			startTime=$(date +%s%3N)
			$cmd
			filename=$(basename -- "$file")
			echo -e "$filename\t$lvl\t$t\t$(($(date +%s%3N)-$startTime))"
		done
	done
done
for lvl in {1,2,3,4,5,6,7,8,9}; do
	cmd="./_verify.sh $lvl gzip 0 $indir"
	#echo "Running command: $cmd"
	startTime=$(date +%s%3N)
	$cmd
	echo -e "gzip\t$lvl\t1\t$(($(date +%s%3N)-$startTime))"
done

