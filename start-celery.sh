#! /bin/sh -l
basedir=$(dirname $0)
homedir=$(echo $0 | sed -e 's_\(/home/[^/]*\).*_\1_')
. $homedir/webslat-env/bin/activate
export LD_LIBRARY_PATH=$homedir/SLAT/linux/lib
export PYTHONPATH=$homedir/SLAT/linux/lib
cd $basedir/webslat
celery -A celery_tasks worker
