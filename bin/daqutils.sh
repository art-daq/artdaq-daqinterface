
# JCF, Dec-3-2015

# This script is not intended to be executed or sourced directly;
# rather, it contains utility functions currently used both by
# just_do_it.sh and auto_file_close.sh


# check_for_state will take two arguments: the name of the state to be
# checked for, and the name of the variable which will be filled with
# the boolean result of whether or not the DAQ is in the desired state
# (effectively a pass-by-reference)

if [[ -z $scriptdir ]]; then
    scriptdir="$(dirname "$0")"
fi

function check_for_state() {
    local stateName=$1
    local __stateBoolVarname=$2
    local stateTrue="0"
    status_script=$scriptdir/status.sh

    res=$( $status_script  | tail -1 | tr "'" " " | awk '{print $2}' )

    if [[ "$res" == "$stateName" ]]; then
	stateTrue="1"
    fi
    eval $__stateBoolVarname="'$stateTrue'"
}

# wait_until_no_longer essentially hangs until it discovers via
# "lbnecmd check" that the DAQ is no longer in the state passed to it
# as an argument

function wait_until_no_longer() {
    local state=$1

    while [[ "1" ]]; do
      sleep 1
      still_in_state="0"

      check_for_state $state still_in_state

      if [[ "$still_in_state" != "1" ]]; then
	  break
      fi

    done
}
