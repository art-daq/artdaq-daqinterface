#!/bin/bash


if (( $# != 2 && $# != 3)) ; then
     echo "Usage: $0 <run number> <process label> (optional, any third argument will open the logfile)"
     exit 1
fi

runnum=$1
proclabel=$2
examine=$3

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh

if [[ "$runnum" =~ ^[0-9]+$ ]]; then
    echo "Run number is $runnum"
else
    echo "Error: run number \"$runnum\" isn't an integer; exiting..." >&2
    exit 1
fi

echo "artdaq process label is $proclabel"

metadata_file=$recorddir/$runnum/metadata.txt

if [[ ! -e $metadata_file ]]; then
    echo "Unable to find expected metadata file $metadatafile" >&2
    exit 1
fi

for procname in boardreader eventbuilder routingmanager datalogger dispatcher; do

    logfiles=$( sed -r -n '/'$procname' logfiles:/,/^$/p' $metadata_file | sed '1d;$d')

    for logfile in $logfiles; do

	if [[ -n $( echo $logfile | sed -r -n '/'$proclabel'-/p') ]]; then

	    host=$( echo $logfile | awk 'BEGIN{FS=":"}{print $1}' )
	    filename=$( echo $logfile | awk 'BEGIN{FS=":"}{print $2}' )

	    if [[ -n $examine && "$examine" != "0" ]]; then

		if [[ "$host" == "$HOSTNAME" || "$host" == "localhost" ]]; then
		    if [[ -e $filename ]]; then
			less $filename
			exit 0
		    else
			cat <<EOF

$metadata_file lists
$filename
as being on this host but it doesn't appear to exist (any longer)

EOF

		    fi
		else
		    ssh -f $host "if [[ -e $filename ]]; then cat $filename ; else echo \"File $filename doesn't appear to exist (any longer)\" ; fi"
		    exit 0
		fi
	    else

		echo $logfile
		exit 0
	    fi
	fi
    done
done

echo "Unable to find logfile corresponding to process \"$proclabel\" from run $runnum" >&2
exit 1
