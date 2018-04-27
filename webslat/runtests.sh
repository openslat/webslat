#! /bin/sh
rm -f test_db.sqlite3
./manage.py test --keepdb slat
