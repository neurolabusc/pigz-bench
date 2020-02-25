#!/bin/bash
# ./_decompress.sh pigz indir #time decompression of all gz files in indir
set -eu

if [ $# -lt 1 ]; then
	exenam=gzip
else
	exenam=$1
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
if [ $# -gt 1 ]; then
	indir=$2
fi

if [ ! -d "$indir" ]; then
 echo "Error: Unable to find $indir"
 exit 1
fi

#for i in {1..2}; do
#echo "Iteration $i"
for file in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
	if [ "${file##*.}" = "gz" ]; then
		#echo "$file "
		cmd="$exenam -d -k -f $file"
		#echo "Running command: $cmd"
		$cmd
	fi
	#! python -m json.tool "$file" > /dev/null || echo " --  Valid."
done
#done

