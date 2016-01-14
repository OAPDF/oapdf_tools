#! /bin/bash

while True; do
python getPDF.py not.txt
mv not.txt hehehe.txt
./checkdone.sh hehehe.txt
mv Done/*.pdf Done/Done/
sleep 30
done