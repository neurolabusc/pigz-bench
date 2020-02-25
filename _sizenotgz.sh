#!/bin/bash
# ./_sizenotgz.sh indir      #size of non-gz files
# ./_sizenotgz.sh indir reps #size of non-gz files multiplied by reps
set -eu

if [ -z ${basedir:-} ]; then
    basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi
indir=${basedir}/corpus
if [ $# -gt 0 ]; then
	indir=$1
fi

if [ ! -d "$indir" ]; then
 echo "Error: Unable to find $indir"
 exit 1
fi

sum=0
for file in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
	if [[ "$OSTYPE" == "darwin"* ]]; then
		sz=$(stat -f%z "$file")
	else
		sz=$(stat -c%s "$file")
	fi
	if [ ! "${file##*.}" = "gz" ]; then
		sum=$(($sum + $sz))
	fi
done

if [ $# -gt 1 ]; then
	reps=$2
	sum=$(($sum * $reps))
fi
echo -e "uncompressed bytes tested:\t$sum"
#exit $sum #return code 16 bit
