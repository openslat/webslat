#! /bin/sh
rm -f test_components.sqlite3 test_slat_constants.sqlite3 test_db.sqlite3

for mode in True False; do
    echo Testing with SINGLE_USER_MODE=${mode}
    sed 's/SINGLE_USER_MODE.*$/SINGLE_USER_MODE = '${mode}'/' webslat/settings.py \
        > webslat/temp_settings.py

    cp components.sqlite3 test_components.sqlite3
    cp slat_constants.sqlite3 test_slat_constants.sqlite3

    ./manage.py test --keepdb slat --settings webslat.temp_settings
    
    rm -f test_components.sqlite3 test_slat_constants.sqlite3 test_db.sqlite3 \
       webslat/temp_settings.py
done
