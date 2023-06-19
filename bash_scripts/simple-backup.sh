#!/bin/sh
LOGFILE=/data/s4509412/backup-compute-server-logs-$1.txt
date > $LOGFILE
rsync -a /data/s4509412/data /data/s4509412/$1 --delete --verbose >> $LOGFILE
