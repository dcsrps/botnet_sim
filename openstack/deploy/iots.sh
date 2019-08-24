#! /bin/bash


key="${1}"
case ${key} in
start)
	source ../../demo-openrc.sh
	echo "	Starting iot vms."
        openstack server list -c ID -c Name | grep iot | awk '{print $2}' | xargs -I {} openstack server start {}
	;;
stop)
	source ../../demo-openrc.sh
	echo "	Stopping iot vms."
        openstack server list -c ID -c Name | grep iot | awk '{print $2}' | xargs -I {} openstack server stop {}
        ;;
create)
	if [ $# -lt 2 ]
	then
        	echo "$0 <create> <gateway count>"
        	exit
	fi

	echo "Checking network existence."
	source ../../demo-openrc.sh
	openstack network list -c Name | grep gateway;
        if test $? -eq 0; 
	then
		echo "	Creating iot vms."
		INPUTPARAM="${2}"
		min_iot=5
		max_iot=10
		counter=1
		while [ $counter -le $INPUTPARAM ];do
			net=gateway_$counter
			cnt=`shuf -i $min_iot-$max_iot -n 1`
			echo "	Creating $cnt iot instances at : $net."
			openstack server create --flavor cirros256 --image iot --network $net --min $cnt --max $cnt iot$counter > /dev/null
			((counter++))
		done
	else
		echo "Networks are not created. Use networks.sh."
                exit
	fi
        ;;

delete)
	source ../../demo-openrc.sh
	echo "	Deleting iot vms."
	openstack server list -c ID -c Name | grep iot | awk '{print $2}' | xargs -I {} openstack server delete {}
        ;;
status)
	source ../../demo-openrc.sh
        echo "  Status of iot vms."
        openstack server list -c Name -c Status | grep 'iot'
	;;
*)    # unknown option
        echo "Unknown option."
	echo "$0 <create> <gateway count>"
	echo "$0 <delete/start/stop/status>"
        ;;
esac
