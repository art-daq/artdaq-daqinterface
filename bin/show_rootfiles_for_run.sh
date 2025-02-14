#!/bin/bash


if [[ $# != 1 && $# != 2 ]] ; then
     echo "Usage: $0 <run number> (first N events -- default 0)"
     exit 1
fi

runnum=$1
nevents=0

if [[ -n $2 ]]; then
    nevents=$2
fi

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh


if [[ "$runnum" =~ ^[0-9]+$ ]]; then
    echo "Run number is $runnum"
else
    echo "Error: run number \"$runnum\" isn't an integer; exiting..." >&2
    exit 1
fi

if [[ "$nevents" =~ ^[0-9]+$ ]]; then
    echo "Will show the first $nevents events from the root file(s) (if any) produced in the run"
else
    echo "Error: number of events to display \"$nevents\" isn't an integer; exiting..." >&2
    exit 1
fi

if [[ ! -d $recorddir/$runnum ]]; then
    echo "Unable to find the expected run record directory \"$recorddir/$runnum\" associated with run $runnum; exiting..." >&2
    exit 1
fi

for file in $recorddir/$runnum/*.fcl ; do

proclabel=$( echo $file | sed -r "s!^.*/([^/]+)\.fcl.*!\1!" )

sedline='s/^\s*fileName\s*:\s*(\S+\.root)\s*/\1/p'

nmatches=$( sed -r -n $sedline $file | wc -l )

if (( $nmatches == 0 )); then
    continue
elif (( $nmatches == 1 )); then

    tablename=$( cat $file | grep -vE "^\s*#" | tr "\n" " " | sed -r 's/^.*\s+(\S+)\s*:\s*\{[^}]*fileName[^}]*\.root.*/\1/' )
    #echo "tablename is $tablename in $proclabel"

    modules_grep_result=$( cat $file | tr "\n" " " | sed -r -n '/.*my_output_modules\s*:\s*\[[^]]*'$tablename'/p' )

    if [[ -z $modules_grep_result ]]; then
	continue
    fi

    file_format=$( sed -r -n $sedline $file )

    runnum_format=$( echo $file_format | sed -r -n 's/.*(%0[0-9])[rR].*/\1d/p' )

    if [[ -z $runnum_format ]]; then
	runnum_format=$( echo $file_format | sed -r -n 's/.*(%)[rR].*/\1d/p' )
    fi

    if [[ -n $runnum_format ]]; then
	runnum_token=$( printf $runnum_format $runnum )
	file_format=$( echo $file_format | sed -r 's/%0[0-9][rR]/'$runnum_token'/' )
	file_format=$( echo $file_format | sed -r 's/%[rR]/'$runnum_token'/' )
    fi

    file_format=$( echo $file_format | sed -r 's/%[^_\.]+/\*/g' )
    file_format=$( echo $file_format | sed -r 's/"//g' )

    if [[ -e $recorddir/$runnum/ranks.txt ]]; then
	prochost=$( sed -r -n 's/^(\S+)\s+([0-9]+)\s+'$proclabel'.*/\1/p' $recorddir/$runnum/ranks.txt )

	if [[ -n $prochost ]]; then
	    cmd="ls -l $file_format"

	    if (( $nevents > 0 )); then
		cmd="$cmd ; echo ; if [[ -z \$( type rawEventDump 2>/dev/null ) ]]; then \
if [[ \"$( grep -El "^\s*alias rawEventDump" $recorddir/$runnum/setup.txt )\" != \"\" ]] ; then \
  echo Using the rawEventDump alias found in $recorddir/$runnum/setup.txt ; \
  . $recorddir/$runnum/setup.txt > /dev/null ; \
  eval \$( alias | sed -r -n \"s/^alias rawEventDump=.(.*).$/\1/p\" ) \$( ls -tr1 $file_format | head -1 ) -n $nevents ; \
else \
  echo -An alias for rawEventDump is not found in $recorddir/$runnum/setup.txt or in the environment ; \
  echo -Will try to run a generic, experiment-independent version of rawEventDump ; \
  echo -Will source the DAQ setup script in order to set up art \($recorddir/$runnum/setup.txt\) ; \
  . $recorddir/$runnum/setup.txt ; \
  art -c $ARTDAQ_DAQINTERFACE_DIR/docs/rawEventDump.fcl \$( ls -tr1 $file_format | head -1 ) -n $nevents  ; \
fi ; \
                     else \
echo Using the rawEventDump which is already available, if a rawEventDump alias exists in $recorddir/$runnum/setup.txt it will be ignored ; \
rawEventDump \$( ls -tr1 $file_format | head -1 ) -n $nevents ; \
                     fi ; \
$cmd "
	    fi

	    echo
	    echo
	    echo
	    echo =======================================${prochost}=======================================
	    if [[ "$prochost" != "$HOSTNAME" ]]; then
		cmd="ssh $prochost '"$cmd"' "
	    fi
	    eval $cmd

	    if [[ "$?" != "0" ]]; then

		cat <<EOF

The command
"$cmd"
returned nonzero; this almost certainly means you
won't get the info you want about the root file, if any, written by
the $proclabel process on $prochost for run $runnum.

EOF

	    fi

	    echo ==============================================================================================
	else
	    cat<<EOF >&2

Unable to determine host that artdaq process $proclabel from run
$runnum ran on based on examination of
$recorddir/$runnum/ranks.txt. Exiting...

EOF
		exit 1
	fi

    else
	echo "Unable to find expected artdaq process info file \"$recorddir/$runnum/ranks.txt\"; exiting..." >&2
	exit 1
    fi

elif (( $nmatches > 1 )); then
    echo "Error: found more than one potential root file listed in $file; exiting..." >&2
    sed -r -n $sedline $file >&2
    exit 1
fi

done
