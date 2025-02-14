
# Make sure the logic to derive DAQInterface port # from partition #
# is the same as in source_me!

export DAQINTERFACE_PORT=$(( $ARTDAQ_BASE_PORT + $DAQINTERFACE_PARTITION_NUMBER * $ARTDAQ_PORTS_PER_PARTITION ))


function list_daqinterfaces() {

ps aux | grep "python.*daqinterface.py" | grep -v grep | awk '{ print "DAQInterface instance was launched at "$9" by "$1" in partition "$14" listening on port "$NF  }'

}

num_daqinterfaces=$( list_daqinterfaces | wc -l )

function port_disclaimer_message() {

if (( $num_daqinterfaces > 1 )); then

cat <<heredoc

This command will be sent to a DAQInterface instance in partition
$DAQINTERFACE_PARTITION_NUMBER listening on port $DAQINTERFACE_PORT if it exists; to instead send to a
DAQInterface instance on another partition, execute
"export DAQINTERFACE_PARTITION_NUMBER=<desired partition number>"

heredoc

    list_daqinterfaces
fi

}

function daqinterface_preamble() {

if (( $num_daqinterfaces > 1)); then
    port_disclaimer_message
elif (( $num_daqinterfaces == 0)); then

cat <<heredoc

No DAQInterface instances are found to exist; will do
nothing. Existing DAQInterface instances can be shown by the
"listdaqinterfaces.sh" command

heredoc
    exit 140
fi

}

