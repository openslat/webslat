#! /bin/sh -l
. /home/webslat-user/.profile
cd /home/webslat-user
. ./webslat-env/bin/activate
cd webslat/webslat
celery -A celery_tasks worker
