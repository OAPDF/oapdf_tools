#! /bin/bash
ISSN="1091-6490"
maxatime="500"
logfile="result.log"

### When first time to run, cancel commend the following: 
#echo "## Now Get PDF for doi: 10.1073/pnas.052143799 Done! Next: 0" > $logfile

while [ 'a' = 'a' ];do
nextitem=`grep "Done" $logfile | tail -n 1 |awk '{print $10}'`
if [ -z $nextitem ];then
nextitem="0"
fi
./crossget.sh $ISSN $nextitem $maxatime | tee -a $logfile

#pdfcount=`ls Done/*.pdf | wc -l`
#if [ $pdfcount -gt 300 ];then
#ts=`date +%s`
#cd Done
#tar -cz --remove-files -f zhaozx@gateway.hpcc.msu.edu:~/GetPDF/PNAS/
#scp PNAS_$ts.tar.gz user@server_name:~/PATH
#rm PNAS_$ts.tar.gz
#cd ..
#else
sleep 10
#fi

done
