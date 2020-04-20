#!/bin/bash

host=$1

if [ "host" != "" ]
then
  rsync -e "ssh -p 4222" -av --cvs-exclude --delete ./ root@${host}:/tmp/alignak-backend
  ssh root@${host} "pip3 install -U /tmp/alignak-backend; systemctl restart alignak-backend"
else
  echo "You must specify host params... Ex. $ tryin.sh"
fi
