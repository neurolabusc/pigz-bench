#!/bin/bash
# ./_sizefrac.sh indir #size of gz files as percent of non gz files

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
#sleep 1
sum=0
sumgz=0
for file in $(find ${indir}/* -maxdepth 1 -type f); do # only regular file in the current dir
	if [[ "$OSTYPE" == "darwin"* ]]; then
		sz=$(stat -f%z "$file")
	else
		sz=$(stat -c%s "$file")
	fi
	if [ ! "${file##*.}" = "gz" ]; then
		sum=$(($sum + $sz))
	else
		sumgz=$(($sumgz + $sz))	
	fi
done
#echo $sumgz $sum ${sumgz}/${sum}
pct=$((1000 * sumgz / sum))
if [ ! -z "$(ls $indir)" ]; then
 rm -f $indir/*.gz
fi
exit $pct

