#!/bin/env bash

# JCF, Nov-27-2017

# For the time being, at least, this script operates under the
# assumption that the *.root file is accessible on the local
# host. Note that there may be a danger of confusion if you wrote a
# file to a different host during the run, but there's a file with an
# identical name on the localhost

if [[ $# != 1 ]]; then
    echo "Please pass run number as argument" >&2
    exit 10
fi

runnum=$1

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh
. $ARTDAQ_DAQINTERFACE_DIR/bin/diagnostic_tools.sh

setupscript=$recorddir/$runnum/setup.txt

if [[ -e $setupscript ]]; then

    if [[ -n $PRODUCTS ]]; then

	ups_is_setup=false  # Needed for unset function

	for proddir in $( echo $PRODUCTS | tr ":" "\n" ) ; do

	    if [[ -e $proddir/setup && -d $proddir/ups ]]; then
		. $proddir/setup
		ups_is_setup=true
	    fi
	done

	if ! $ups_is_setup ; then
	    echo "Unable set up product \"ups\" given products directories $PRODUCTS. ups is needed for the unsetup function, so will exit..." >&2
	    exit 100
	fi


	# Ron's unsetup function

	for pp in `printenv | sed -ne '/^SETUP_/{s/SETUP_//;s/=.*//;p}'`;do
            test $pp = UPS && continue;
            prod=`echo $pp | tr 'A-Z' 'a-z'`;
            eval "tmp=\${SETUP_$pp-}";
            test -z "$tmp" && echo already unsetup && continue;
            unsetup -j $prod;
	done
    fi

    . $setupscript 2>&1 > /dev/null

    if [[ "$?" != "0" ]]; then
	echo "Nonzero value returned by source of ${setupscript}; exiting..."
	exit 60
    fi

    echo
    echo "Sourced $setupscript"

else

    echo "WARNING: unable to find setup script originally used for run $runnum (looked for ${setupscript}); will try to set up art with package_setup.sh" >&2

    . $ARTDAQ_DAQINTERFACE_DIR/bin/package_setup.sh art

    art_retval=$?

    if [[ "$art_retval" != "0" ]]; then
	echo "Problem attempting to setup art package" >&2
	exit 40
    fi
fi


# We'll actually just look at the first file if there are many

for file_location in $( file_locations ); do

    rootfile_dir=$( echo $file_location | sed -r -n 's/.*:(.*)/\1/p' )
    rootfile=$(ls -tr1 ${rootfile_dir}/*$(printf "%06d" $runnum)*_*.root 2>/dev/null| tail -1 )

    if [[ -n $rootfile ]]; then
	break
    fi
done

scriptname=$( basename "$0" )

if [[ -z $rootfile ]]; then

    cat>&2<<EOF

    Unable to find a root file for run #${runnum} in directory
    "${rootfile_dir}"; note that this script ($scriptname) needs to be
    run on one of the hosts to which rootfiles were written

EOF


    exit 20
fi

if [[ -z $( which config_dumper ) ]]; then
    echo
    echo "Unable to find config_dumper; you need to have your environment properly set up" >&2
    exit 30
fi

temporary_daqinterface_boot_file=/tmp/$(uuidgen)
temporary_metadata_file=/tmp/$(uuidgen)

echo "NOTE: erasing any output to stderr from config_dumper; as long
as config_dumper works correctly this won't affect the results of the
test"

set -o pipefail   # See, e.g., https://stackoverflow.com/questions/1221833/pipe-output-and-capture-exit-status-in-bash

config_dumper -P $rootfile 2> /dev/null | sed -r 's/\\n/\n/g'  | sed -r '1,/boot: "contents/d;/^\s*\\"\s*$/,$d;s/\\"/"/g'  > $temporary_daqinterface_boot_file

if [[ "$?" != "0" ]]; then
    echo "An error occurred in the config_dumper pipe command, aborting..."
    exit 1
fi

if [[ ! -s $temporary_daqinterface_boot_file ]]; then
    echo "It appears no DAQInterface boot info was saved in $rootfile"
fi

config_dumper -P $rootfile 2> /dev/null  | sed -r 's/\\n/\n/g;s/\\"/"/g'  | sed -r '1,/metadata: "contents/d;/^\s*"\s*$/,$d' > $temporary_metadata_file

if [[ "$?" != "0" ]]; then
    echo "An error occurred in the config_dumper pipe command, aborting..."
    exit 1
fi

if [[ ! -s $temporary_metadata_file ]]; then
    echo "It appears no metadata info was saved in $rootfile"
fi

run_records_boot_file=$recorddir/$runnum/boot.txt
run_records_metadata_file=$recorddir/$runnum/metadata.txt

if [[ ! -e $run_records_boot_file ]]; then
    echo "Unable to find DAQInterface boot file \"${run_records_boot_file}\"" >&2
    exit 30
fi

if [[ ! -e $run_records_metadata_file ]]; then
    echo "Unable to find metadata file \"${run_records_metadata_file}\"" >&2
    exit 40
fi

# JCF, Jan-24-2017

# We shouldn't complain if there's data added to the metadata file in
# run records that doesn't appear in the saved metadata in the *.root
# file if that data's added after the initialization of the artdaq
# processes - so let's "clean out" variables added later before we
# perform the comparison

cleaned_run_records_metadata_file=/tmp/$(uuidgen)

grep -E -v 'Total events|DAQInterface start time|DAQInterface stop time' $run_records_metadata_file > $cleaned_run_records_metadata_file

res_boot=$( diff --ignore-blank-lines $temporary_daqinterface_boot_file $run_records_boot_file )
res_metadata=$( diff --ignore-blank-lines $temporary_metadata_file $cleaned_run_records_metadata_file )


if [[ -z $res_boot && -z $res_metadata ]]; then
    echo "Data in $rootfile and $recorddir/$runnum agree"
    rm -f $temporary_daqinterface_boot_file $temporary_metadata_file $cleaned_run_records_metadata_file
    exit 0
fi

if [[ -n $res_boot ]]; then
    echo $res_boot
    echo "DAQInterface boot file info inconsistent between $rootfile and $recorddir/$runnum (see above for diff)"
fi

if [[ -n $res_metadata ]]; then
    echo $res_metadata
    echo "Metadata file info inconsistent between $rootfile and $recorddir/$runnum (see above for diff)"
fi

echo temporary_daqinterface_boot_file=$temporary_daqinterface_boot_file
echo temporary_metadata_file=$temporary_metadata_file
echo cleaned_run_records_metadata_file=$cleaned_run_records_metadata_file

rm -f $temporary_daqinterface_boot_file $temporary_metadata_file $cleaned_run_records_metadata_file

exit 50
