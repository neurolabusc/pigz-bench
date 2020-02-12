#!/bin/bash

if [ -z ${basedir:-} ]; then
    basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
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
	for lvl in {3,6,9}; do
		for t in {1,2,4,0}; do		
			cmd="./3test.sh $lvl $file $t"
			#echo "Running command: $cmd"
			startTime=$(date +%s%3N)
			$cmd
			filename=$(basename -- "$file")
			echo -e "$filename\t$lvl\t$t\t$(($(date +%s%3N)-$startTime))"
		done
	done
done
for lvl in {3,6,9}; do
	cmd="./3test.sh $lvl gzip"
	#echo "Running command: $cmd"
	startTime=$(date +%s%3N)
	$cmd
	echo -e "gzip\t$lvl\t1\t$(($(date +%s%3N)-$startTime))"
done

