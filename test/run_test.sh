#!/bin/bash

REPORT_SOURCE="../ossftp,../osssftp"
OMIT_SOURCE="../ossftp/ftpd.py"
RUN_PARAMS="--source=$REPORT_SOURCE --omit=$OMIT_SOURCE"

if [ -f "test-rsa" ];then
rm test-rsa
fi

coverage erase
coverage run $RUN_PARAMS -p login.py
coverage run $RUN_PARAMS -p dir.py
coverage run $RUN_PARAMS -p file.py
coverage run $RUN_PARAMS -p endpoint_test.py
coverage run $RUN_PARAMS -p sftp_test.py
coverage combine
coverage html

rm test-rsa
