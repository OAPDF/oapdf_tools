#! /bin/bash
# file: gitsubmit.sh

comment=$1
if [ -z $comment ];then
comment=regular
fi

git add -A
git commit -am "$comment"
git push origin master
