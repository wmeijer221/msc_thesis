#!/bin/sh
date > ./backup-compute-server-logs-$1.txt
rsync -a /data/s4509412/data /data/s4509412/$1 --delete --verbose >> ./backup-compute-server-logs.txt
