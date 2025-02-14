#!/bin/env bash

if [[ "$#" != 1 ]]; then
    echo "Usage: "$( basename $0 )" <boot file in traditional format>"
    exit 0
fi

bootfile=$1

. $ARTDAQ_DAQINTERFACE_DIR/bin/exit_if_bad_environment.sh

if [[ ! -e $bootfile ]]; then
    cat<<EOF >&2

Error: the boot file you supplied, "$bootfile", does not appear to
exist. Exiting...

EOF

exit 1
fi

if [[ ! -e $DAQINTERFACE_SETUP_FHICLCPP ]]; then
    cat<<EOF >&2

Error: the fhiclcpp setup script referred to by
\$DAQINTERFACE_SETUP_FHICLCPP, "$DAQINTERFACE_SETUP_FHICLCPP", does
not appear to exist. Exiting...

EOF

exit 1
fi

. $DAQINTERFACE_SETUP_FHICLCPP > /dev/null

if [[ -z $( ups active | grep fhiclcpp ) ]]; then

    cat<<EOF >&2

Error: the fhiclcpp setup script "$DAQINTERFACE_SETUP_FHICLCPP" failed
to set up fhiclcpp correctly when sourced. Exiting...

EOF
exit 1
fi

tmpfile=$( mktemp )
cat $bootfile | awk -f $ARTDAQ_DAQINTERFACE_DIR/utils/fhiclize_boot_file.awk > $tmpfile

fhicl-dump -l 0 -c $tmpfile

if [[ "$?" != "0" ]]; then
    cat<<EOF >&2

Error: fhicl-dump returned nonzero, so the fhicl printed out above
should not be used. Perhaps there's a problem with the intermediate
file created with the
$ARTDAQ_DAQINTERFACE_DIR/utils/fhiclize_boot_file.awk script,
$tmpfile. Exiting...

EOF
exit 1
fi

rm -f $tmpfile

exit 0
