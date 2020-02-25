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

#### no need to edit subsequent lines
if [[ "$OSTYPE" == "darwin"* ]]; then
	echo Make sure to "'"brew install coreutils"'"
	shopt -s expand_aliases
	alias date='gdate'
fi
#folder paths
exedir=${basedir}/exe

reps=2;
#./batch.sh
echo -e "Method\tLevel\tThreads\tms\t%"
for file in $exedir/*; do
	for lvl in {3,6,9}; do
		for t in {1,2,4,0}; do	
			cmd="./_test.sh $lvl $file $t $indir $reps"
			#echo "Running command: $cmd"
			startTime=$(date +%s%3N)
			$cmd
			ms=$(($(date +%s%3N)-$startTime))
			cmd="./_sizefrac.sh $indir"
			$cmd
			pct=$(bc <<<"scale=1;$?/10")
			filename=$(basename -- "$file")
			echo -e "$filename\t$lvl\t$t\t$ms\t$pct"
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
	cmd="./_sizefrac.sh $indir"
	$cmd
	pct=$(bc <<<"scale=1;$?/10")
	echo -e "gzip\t$lvl\t1\t$ms\t$pct"
done
#report bytes
./_sizenotgz.sh $indir $reps

