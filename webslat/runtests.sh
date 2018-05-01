#! /bin/sh
rm -f test_components.sqlite3 test_slat_constants.sqlite3 test_db.sqlite3
cp components.sqlite3 test_components.sqlite3
cp slat_constants.sqlite3 test_slat_constants.sqlite3

# Run tests, diescarding SLAT warnings 
./manage.py test --keepdb slat 2> /dev/null

rm test_components.sqlite3 test_slat_constants.sqlite3 test_db.sqlite3
