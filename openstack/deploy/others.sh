#! /bin/bash


key="${1}"
case ${key} in
start)
	source ../../demo-openrc.sh
	echo "	Starting other vms."
        openstack server list -c ID -c Name | grep 'scan\|bot' | awk '{print $2}' | xargs -I {} openstack server start {}
	;;
stop)
	source ../../demo-openrc.sh
	echo "	Stopping other vms."
        openstack server list -c ID -c Name | grep 'scan\|bot' | awk '{print $2}' | xargs -I {} openstack server stop {}
        ;;
create)
	if [ $# -lt 2 ]
	then
        	echo "$0 <create> <bot count>"
        	exit
	fi

	source ../../demo-openrc.sh
	echo "	Creating scanner vm."
	openstack server create --flavor ds512M --image Scanner --network out scan > /dev/null
	
	INPUTPARAM="${2}"
	echo "	Creating bot vms."
	openstack server create --flavor ds512M --image Bot --network out --min $INPUTPARAM --max $INPUTPARAM bot > /dev/null
        ;;

delete)
	source ../../demo-openrc.sh
	echo "	Deleting iot vms."
	openstack server list -c ID -c Name | grep iot | awk '{print $2}' | xargs -I {} openstack server delete {}
        ;;
status)
	source ../../demo-openrc.sh
        echo "  Status of other vms."
        openstack server list -c Name -c Status | grep 'scan\|bot' 
        ;;
*)    # unknown option
        echo "Unknown option."
	echo "$0 <create> <bot count>"
	echo "$0 <delete/start/stop/status>"
        ;;
esac
