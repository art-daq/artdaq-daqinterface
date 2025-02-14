#!/bin/env bash

if [[ "$#" != 1 ]]; then
    echo "Usage: "$( basename $0 )" <boot file in FHiCL format>"
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
fhicl-dump -l 0 -c $bootfile > $tmpfile

if [[ "$?" != "0" ]]; then
    cat<<EOF >&2

Error: fhicl-dump as applied to $bootfile returned nonzero. Illegal
FHiCL syntax in the file? Exiting...

EOF
exit 1
fi

cat $tmpfile | awk -f $ARTDAQ_DAQINTERFACE_DIR/utils/convert_fhicl_dumped_bootfile_to_traditional_format.awk
rm -f $tmpfile

exit 0
