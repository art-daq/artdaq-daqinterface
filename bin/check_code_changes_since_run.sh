#!/bin/env bash

if [[ "$#" != 1 ]]; then
    echo "Usage: "$( basename $0 )" <existing run number>"
    exit 0
fi

runnum=$1

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh

if [[ ! -d $recorddir/$runnum ]]; then
    echo "Unable to find subdirectory \"$runnum\" in $recorddir; exiting..." >&2
    exit 1
fi

daq_setup_script=$( sed -r -n 's/^\s*DAQ\s+setup\s+script\s*:\s*(\S+).*$/\1/p' $recorddir/$runnum/boot.txt )
daq_dir=$( dirname $daq_setup_script )

sourced_daq_setup_script=false

awk '/commit\/version/ ' $recorddir/$runnum/metadata.txt | while read line; do
    package=$( echo $line | awk '{print $1}' )

    if [[ $package =~ DAQInterface ]]; then
	continue
    fi

    package_underscored=$( echo $package | sed -r 's/-/_/g' )

    hash_or_version=$( echo $line | awk '{print $3}' )
    locs_added=$( echo $line | awk '{print $4}' )
    locs_subtracted=$( echo $line | awk '{print $5}' )

    if [[ ${#hash_or_version} == 40 ]]; then

	repo_dir=""

	if [[ -e $daq_dir/srcs/$package ]]; then
	    repo_dir=$daq_dir/srcs/$package
	elif [[ -d $daq_dir/srcs/$package_underscored ]]; then
	    repo_dir=$daq_dir/srcs/$package_underscored
	else
	    echo "Unable to find repository for $package in installation located in $daq_dir" >&2
	fi

	if [[ "$locs_added" != "0" || "$locs_subtracted" != "0" ]]; then

	    cat<<EOF

It's not possible to compare the current code in $repo_dir with the
code used in run $runnum since according to the run record the code
wasn't fully committed at the time of the run.

EOF
	fi



	cd $repo_dir
	hash_and_comment=$( git log --pretty=oneline -1 )
	discovered_hash=$( echo $hash_and_comment | awk '{print $1}' )

	if [[ $discovered_hash != $hash_or_version ]]; then

	    cat <<EOF

Commit hash for $package package is different between that used for
run $runnum and the current git repo, $repo_dir:

EOF

	    echo "Run $runnum: "
	    echo $line | sed -r 's/^.*: //'
	    echo "Current repo: "
	    echo $hash_and_comment
	fi

    else

	type unsetup > /dev/null >& /dev/null

	if [[ "$?" == "0" ]]; then
	    for pp in `printenv | sed -ne "/^SETUP_/{s/SETUP_//;s/=.*//;p}"`; do
		test $pp = UPS && continue; prod=`echo $pp | tr "A-Z" "a-z"`; unsetup -j $prod;
	    done
	fi

	. $daq_setup_script >&2 > /dev/null
	discovered_version=$( ups active | awk '/^'$package_underscored'\s+/ { print $2 }' )

	if [[ $discovered_version != $hash_or_version ]]; then

	    cat <<EOF

Version of $package package is different between that used for
run $runnum and the version currently setup by the setup script $daq_setup_script:

EOF

	    echo "Run $runnum: "
	    echo $hash_or_version
	    echo "Current version: "
	    echo $discovered_version
	fi
    fi

done

exit 0
