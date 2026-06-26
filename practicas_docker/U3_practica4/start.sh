#!/bin/bash
sed -i "s,___TARGET_HOST___,${TARGET_HOST},g" /etc/myprogram/myconfig.conf
tail -f /dev/null
