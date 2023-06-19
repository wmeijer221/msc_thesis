#!/bin/sh

echo Starting back-up!

LOGFILE=/data/s4509412/backup-compute-server-logs-$1.txt
date > $LOGFILE
rsync -a $LOGFILE --delete --verbose >> $LOGFILE

echo Completed back-up!
