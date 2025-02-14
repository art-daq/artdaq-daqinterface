#!/bin/env bash

if (( "$#" != 1 && "$#" != 2)) || [[ "$#" == 2 && "$2" != "--force" ]]; then
	echo "Usage: "$( basename $0 )" <partition number to mopup> (optional \"--force\")"
	exit 1
fi

retval=0 #Innocent until proven guilty
partition=$1

force_cleanup=false
if [[ -n $2 ]]; then
	force_cleanup=true
fi

if ! [[ "$partition" =~ [0-9]+ ]]; then
	echo "Partition number needs to be an integer; exiting..." >&2
	exit 1
fi

if ! $force_cleanup; then

	. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh

	if [[ -n $( listdaqinterfaces.sh | grep -E "\s+[Pp]artition\s+$partition\s+" ) ]]; then

		timeoutsecs=10

		cat<<EOF

A DAQInterface on partition $partition has been found; will confirm
that it's in the "stopped" state via a status.sh call with a
$timeoutsecs second timeout...

EOF

		res=$( timeout $timeoutsecs $ARTDAQ_DAQINTERFACE_DIR/bin/status.sh | tail -1 | tr "'" " " | awk '{print $2}' )

		if [[ "$res" == "stopped" ]]; then

			echo "DAQInterface in \"stopped\" state; will proceed with cleaning up the shared memory blocks"

		elif [[ "$res" == "" ]]; then

			cat <<EOF >&2

No state discovered after calling status.sh, this may be because the
$timeoutsecs second timeout was activated due to a communication
issue. If you want this script to clean up the shared memory blocks
regardless, execute it again with the option "--force"
added. Exiting...

EOF

	exit 1

		elif [[ "$res" != "stopped" ]]; then
			cat<<EOF >&2

After executing status.sh the DAQInterface instance on partition
$partition didn't confirm it's in the "stopped" state (result was
"$res"). If you want this script to clean up the shared memory blocks
regardless, execute it again with the option "--force"
added. Exiting...

EOF
	exit 1
		fi
	fi

fi

token=$(( partition + 1))
hextoken=$( printf "%02x" $token )
#echo "Assuming that partition $partition appears as \"$hextoken\" in the shmem keys..."

num_blocks=$( ipcs | grep -E "^0xee${hextoken}|^0xbb${hextoken}|^0x${hextoken}00" | wc -l )
num_owned_blocks_before=$( ipcs | grep -E "^0xee${hextoken}|^0xbb${hextoken}|^0x${hextoken}00" | grep $USER | wc -l )

if (( $num_blocks != $num_owned_blocks_before )); then

	cat<<EOF >&2

WARNING: it appears that only $num_owned_blocks_before of $num_blocks shared
memory blocks associated with partition $partition are actually owned
by the user (\$USER == "$USER"); cleanup will be incomplete...

EOF
	retval=10
fi

function get_shmids() {
	ipcs | grep -E "^0xee${hextoken}|^0xbb${hextoken}|^0x${hextoken}00" | grep $USER | awk '{print $2}'
}

function kill_art() {
	pids=`ps -fu $USER|grep "art -c"|grep "partition_$partition"|awk '{print $2}'`
	echo "Killing art processes `echo $pids|tr '\n' ' '`"
	kill $pids
	sleep 5
	for pid in $pids; do
		kill -0 $pid
		if [ $? -eq 0 ]; then
			echo "Killing with force: $pid"
			kill -9 $pid
		fi
	done
}
kill_art

owner_pids=""

for shmid in $( get_shmids ); do
	nattached=$( ipcs | awk '{ if ("'$shmid'" == $2) { print $6 } }' )

	if ! [[ "$nattached" =~ ^[0-9]+$ ]]; then
		echo "Surprising error - attempt to determine number of attached processes to shared memory block with id $shmid did not yield an integer" >&2
		exit 1
	fi

	if (( nattached > 0 )); then
		owner_pid=$( ipcs -mp | awk '{ if ("'$shmid'" == $1) { print $4 } }' )

		if [[ "$owner_pid" =~ ^[0-9]+$ ]]; then
			if ! [[ "$owner_pids" =~ " $owner_pid " ]]; then
				owner_pids=" $owner_pid $owner_pids"
			fi
		else
			echo "Unable to get integer pid for owner of shared memory block with id $shmid" >&2
			exit 1
		fi
	fi
done

for owner_pid in $owner_pids; do
	echo "Will try to kill the following process since it owns at least one shared memory block:"
	ps aux | grep -E "^\S+\s+$owner_pid\s+"
	kill $owner_pid
done

ipcs

for shmid in $( get_shmids ); do

	echo "Removing shared memory block with id $shmid"
	ipcrm -m $shmid
done

num_owned_blocks_after=0
for shmid in $( get_shmids ); do
	num_owned_blocks_after=$(( num_owned_blocks_after + 1 ))
done

if (( $num_owned_blocks_after != 0 )); then
	retval=11
fi

echo $((num_owned_blocks_before - num_owned_blocks_after))" of $num_owned_blocks_before original shared memory blocks have been cleaned up (all of them should have been cleaned up)"

exit $retval
