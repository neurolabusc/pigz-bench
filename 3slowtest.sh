#!/bin/bash
# 3slowtest.sh   #download the SilesiaCorpus and test compression performance
#
# https://github.com/MiloszKrajewski/SilesiaCorpus
git clone https://github.com/MiloszKrajewski/SilesiaCorpus
cd SilesiaCorpus
unzip -o '*.zip'
rm *.zip
cd ..
./2test.sh SilesiaCorpus