
# JCF, Jul-24-2019: This script is meant to be sourced at the top of
# executable scripts which expect the DAQInterface environment to be
# set up

if [[ -z $DAQINTERFACE_STANDARD_SOURCEFILE_SOURCED ]]; then
    cat <<EOF >&2

It appears you haven't set up the DAQInterface environment - e.g.,
various environment variables which DAQInterface instances and the
scripts which control them need in order to know how to behave are
unset. Please read the DAQInterface manual at
https://cdcvs.fnal.gov/redmine/projects/artdaq-utilities/wiki/Artdaq-daqinterface
to learn how to set up the environment. Exiting...

EOF

exit 1

fi
