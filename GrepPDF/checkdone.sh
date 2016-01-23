#! /bin/bash
# Check doi list.. generate not.txt for files not done
# Need doi list input file
dos2unix $1
echo -n > not.txt
for line in `cat $1`
do
if [ -z $line ];then
	continue;
fi
pre=${line:0:7}
post=${line:8}
if [ ! -f Done/${pre}_${post}.pdf ];then
if [ ! -f Accept/${pre}_${post}.pdf ];then
	echo "${pre}/${post}" >> not.txt
fi
fi
done
