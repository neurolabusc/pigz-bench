#!/bin/bash
# ./6speed_size.sh                    #test performance for data in default folder "corpus"
# ./6speed_size.sh SilesiaCorpus.tar  #test performance for data in file "SilesiaCorpus" 

echo This script requires zstd, bzip2 and gzip
basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exedir=${basedir}/exe
tarfile=$basedir/SilesiaCorpus.tar
if [ $# -gt 0 ]; then
	tarfile=$1
fi
if [ ! -d "$exedir" ]; then
        echo >&2 "I require $exedir but it's not installed (run 1compile.sh first).  Aborting."
        exit 1
fi
if [ ! -f "$tarfile" ]; then
	#echo >&2 "I require $tarfile but it's not installed.  Will download."
	tardir=$basedir/SilesiaCorpus
	if [ ! -d "$tardir" ]; then
		git clone https://github.com/MiloszKrajewski/SilesiaCorpus

	fi
	cd $tardir
	unzip -o '*.zip'
	rm *.zip
	cd $basedir
	cmd="tar -cf $tarfile $tardir/"
	echo $cmd
	$cmd
fi
if [[ "$OSTYPE" == "darwin"* ]]; then
	echo Make sure to "'"brew install coreutils"'"
	shopt -s expand_aliases
	alias date='gdate'
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
	bytes=$(stat -f%z "$tarfile")
else
	bytes=$(stat -c%s "$tarfile")
fi
#threads=0 test default performance
#./batch.sh
echo -e "Method\tLevel\tms\tsize\tmbs"
#bytesPerMegabyte: you could also choose 1024x1024
bytesPerMegabyte=1000000
#1000 ms per second
scale=$((1000 * $bytes / $bytesPerMegabyte))
#test pigz
tarfileExt=$tarfile.gz
for file in $exedir/*; do
	for lvl in {1,2,3,4,5,6,7,8,9}; do
		cmd="$file -f -k -$lvl $tarfile"
		startTime=$(date +%s%3N)
		$cmd
		ms=$(($(date +%s%3N)-$startTime))
		if [[ "$OSTYPE" == "darwin"* ]]; then
			bytesz=$(stat -f%z "$tarfileExt")
		else
			bytesz=$(stat -c%s "$tarfileExt")
		fi
		pct=$((1000 * bytesz / bytes))
		pct=$(bc <<<"scale=1;$pct/10")
		filename=$(basename -- "$file")
		mbs=$(($scale / $ms))
		echo -e "$filename\t$lvl\t$t\t$ms\t$pct\t$mbs"
	done
done
#test gzip
file=gzip
#for lvl in {1,2}; do
for lvl in {1,2,3,4,5,6,7,8,9}; do
	cmd="$file -f -k -$lvl $tarfile"
	startTime=$(date +%s%3N)
	$cmd
	ms=$(($(date +%s%3N)-$startTime))
	if [[ "$OSTYPE" == "darwin"* ]]; then
		bytesz=$(stat -f%z "$tarfileExt")
	else
		bytesz=$(stat -c%s "$tarfileExt")
	fi
	pct=$((1000 * bytesz / bytes))
	pct=$(bc <<<"scale=1;$pct/10")
	filename=$(basename -- "$file")
	mbs=$(($scale / $ms))
	echo -e "$filename\t$lvl\t$t\t$ms\t$pct\t$mbs"
done
#test zstd
tarfileExt=$tarfile.zst
file=zstd
for lvl in {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19}; do
	cmd="$file -T0 -q -f -k -$lvl $tarfile"
	startTime=$(date +%s%3N)
	$cmd
	ms=$(($(date +%s%3N)-$startTime))
	if [[ "$OSTYPE" == "darwin"* ]]; then
		bytesz=$(stat -f%z "$tarfileExt")
	else
		bytesz=$(stat -c%s "$tarfileExt")
	fi
	pct=$((1000 * bytesz / bytes))
	pct=$(bc <<<"scale=1;$pct/10")
	filename=$(basename -- "$file")
	mbs=$(($scale / $ms))
	echo -e "$filename\t$lvl\t$t\t$ms\t$pct\t$mbs"
done
#test pbzip2
tarfileExt=$tarfile.bz2
file=pbzip2
for lvl in {1,2,3,4,5,6,7,8,9}; do
	cmd="$file -q -f -k -$lvl $tarfile"
	startTime=$(date +%s%3N)
	$cmd
	ms=$(($(date +%s%3N)-$startTime))
	if [[ "$OSTYPE" == "darwin"* ]]; then
		bytesz=$(stat -f%z "$tarfileExt")
	else
		bytesz=$(stat -c%s "$tarfileExt")
	fi
	pct=$((1000 * bytesz / bytes))
	pct=$(bc <<<"scale=1;$pct/10")
	filename=$(basename -- "$file")
	mbs=$(($scale / $ms))
	echo -e "$filename\t$lvl\t$t\t$ms\t$pct\t$mbs"
done
