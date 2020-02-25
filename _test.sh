#!/bin/bash
# ./_test.sh 7 pigz 3 indir reps   #use pigz, compression level 7, 3 threads, compress files in folder dir, repeated reps times
# ./_test.sh 7 pigz 3 indir        #use pigz, compression level 7, 3 threads, compress files in folder dir
# ./_test.sh 7 pigz 3              #use pigz, compression level 7, 3 threads
# ./_test.sh 7 pigz                #use pigz, compression level 7
# ./_test.sh 7                     #use gzip, compression level 7
# ./_test.sh                       #use gzip, compression level 6
# Fail if anything not planed to go wrong, goes wrong
set -eu

if [ $# -lt 1 ]; then
	level=6
else
	level=$1
fi
if [ $# -lt 2 ]; then
	exenam=gzip
else
	exenam=$2
fi
if [ $# -lt 3 ]; then
	threads=0
else
	threads=$3
fi
# Check inputs.
# Test if command exists.
exists() {
    test -x "$(command -v "$1")"
}
exists $exenam ||
    {
        echo >&2 "I require $exenam but it's not installed (run 1compile.sh first).  Aborting."
        exit 1
    }


if [ -z ${basedir:-} ]; then
    basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi
indir=${basedir}/corpus
if [ $# -gt 3 ]; then
	indir=$4
fi
reps=1
if [ $# -gt 4 ]; then
	reps=$5
fi
if [ ! -d "$indir" ]; then
 echo "Error: Unable to find $indir"
 exit 1
fi
for (( i=1; i<=$reps; i++ )); do
	#echo "Iteration $i"
	for file in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
		if [ ! "${file##*.}" = "gz" ]; then
			#echo "$file "
			if [ $threads -lt 1 ]; then
				cmd="$exenam -$level -f -k $file"
			else
				cmd="$exenam -p $threads -f -k -$level $file"
			fi
			#echo "Running command: $cmd"
			$cmd
		fi
	done
done


