# ELF, 10/23/2019: These are the currently-supported experiment-defined hooks.
# To override, define these functions in "daqinterface_overrides_for_experiment.py" and
# then set DAQINTERFACE_OVERRIDES_FOR_EXPERIMENT_MODULE_DIR to the directory containing
# that file in $DAQINTERFACE_USER_SOURCEFILE .


def perform_periodic_action_base(self):
    pass


def start_datataking_base(self):
    pass


def stop_datataking_base(self):
    pass


def do_enable_base(self):
    pass


def do_disable_base(self):
    pass


def check_config_base(self):
    pass
