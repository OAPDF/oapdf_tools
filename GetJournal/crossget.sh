#! /bin/bash
# Use as crossget.sh ISSN start_number max_try_a_time

if [ ! -z $1 ];then
        ISSN=$1
else
	echo "No ISSN is given!"
	exit 1
fi

start=0
if [ ! -z $2 ];then
        start=$2
fi

maxatime=300
if [ ! -z $3 ];then
        maxatime=$3
fi

##127499 total
#for i in `seq $start 100 10500`;do
        python GetOAJournalPage.py $ISSN $start $maxatime
        #mv *.pdf Done
#done
