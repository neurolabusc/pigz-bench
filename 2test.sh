#!/bin/bash

if [ -z ${basedir:-} ]; then
    basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

#### no need to edit subsequent lines

#folder paths
exedir=${basedir}/exe


#./batch.sh
for file in $exedir/*; do
	for lvl in {3,6,9}; do
		for t in {1,2,0}; do		
			cmd="time ./3test.sh $lvl $file $t"
			echo "Running command: $cmd"
			time $cmd
		done
	done
done
for lvl in {3,6,9}; do
	cmd="time ./3test.sh $lvl gzip"
	echo "Running command: $cmd"
	time $cmd
done

