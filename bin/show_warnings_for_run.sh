#!/bin/bash

if [ $# != 1 ] ; then
     echo "Usage: $0 <run #>"
     echo
     exit 1
fi

runnum=$1

echo

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh

metadata_file=$recorddir/$runnum/metadata.txt

if [[ ! -e $metadata_file ]]; then
    echo "Unable to find expected metadata file $metadatafile" >&2
    exit 1
fi

run_start_time=$( sed -r -n "s/DAQInterface start time:\s*(.*)/\1/p" $metadata_file )
run_stop_time=$( sed -r -n "s/DAQInterface stop time:\s*(.*)/\1/p" $metadata_file )

if [[ -z $run_start_time ]]; then
    run_start_time="unknown"
fi

if [[ -z $run_stop_time ]]; then
    run_stop_time="unknown"
fi

disclaimer="Be aware that warnings/errors are shown for ALL runs which appear in run ${runnum}'s logfile(s). Run $runnum start time is $run_start_time, stop time is $run_stop_time"

method=$( sed -r -n 's/^process management method: (\S+).*/\1/p' $metadata_file)

if [[ "$method" == "pmt" ]]; then
    output=$( show_logfile_for_run.sh $runnum )
elif [[ "$method" == "direct" ]]; then
    proclabels=$( ls $recorddir/$runnum/*.fcl | sort | sed -r 's!.*/([^/]+).fcl$!\1!' )

    output=""
    for proclabel in $proclabels ; do
	output=${output}"@"$( show_logfile_for_process.sh $runnum $proclabel | tail -1 )
    done
    output=$( echo $output | tr "@" "\n" )
else
    echo "Error: unknown process management method \"$method\" obtained from metadata file $metadata_file" >&2
    echo
    exit 1
fi

if [[ "$?" == "0" ]]; then
    echo
    echo $disclaimer
    echo

    for file in $output ; do

	echo
	echo "Examining file \"$file\""

	host=$( echo $file | awk 'BEGIN{FS=":"}{print $1}' )
	filename=$( echo $file | awk 'BEGIN{FS=":"}{print $2}' )

	sedcmd="sed -r -n '{/MSG-e/{N;p};/MSG-w/{N;/Use of services.user parameter set is deprecated/d;/Fast cloning deactivated/d;/Attempted to send metric when/d;/Cannot send init fragment because I haven.t yet received one/d;/Stop Message received/d;/RCVBUF initial/d;p}}' $filename"

	if [[ "$host" == "localhost" || "$host" == "$HOSTNAME" ]]; then
	    if [[ -e $filename ]]; then
		( eval $sedcmd  )
	    fi
	else
	    ssh $host $sedcmd
	fi
    done
    echo
    echo $disclaimer
    echo
else
    echo $output
    exit 1
fi


