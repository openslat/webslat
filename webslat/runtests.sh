#! /bin/sh
rm -f test_components.sqlite3 test_slat_constants.sqlite3 test_db.sqlite3
cp components.sqlite3 test_components.sqlite3
cp slat_constants.sqlite3 test_slat_constants.sqlite3

./manage.py test --keepdb slat

rm -f test_components.sqlite3 test_slat_constants.sqlite3 test_db.sqlite3
