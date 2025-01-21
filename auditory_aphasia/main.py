# Configs will be loaded witin the processes
# from auditory_aphasia.config.config_builder import build_configs
# build_configs()

from auditory_aphasia.config_builder import (build_general_config,
                                             build_system_config)
from auditory_aphasia.main_processes.analysis import run_analysis
from auditory_aphasia.main_processes.familiarization import run_familiarization
from auditory_aphasia.main_processes.main_offline import run_offline
from auditory_aphasia.main_processes.main_online import run_online
from auditory_aphasia.main_processes.setup_testing import main_setup_testing

CONFIG = build_general_config()
SYSTEM_CONFIG = build_system_config()


def run_paradigm():
    print("--------------------------------------------------------")
    print("1: AMUSE online")
    print("2: AMUSE offline")
    print("3: Familarization")
    print("4: Analysis")
    print("5: Setup test")
    print("0: Quit")
    print("--------------------------------------------------------")

    while True:
        main_process_selected = input().strip()

        match main_process_selected:
            case "0":
                return
            case "1":
                print("Starting AMUSE online...")
                run_online(config=CONFIG, system_config=SYSTEM_CONFIG)
            case "2":
                print("Starting AMUSE offline...")
                run_offline(config=CONFIG, system_config=SYSTEM_CONFIG)
            case "3":
                print("Starting familarization...")
                run_familiarization(config=CONFIG, system_config=SYSTEM_CONFIG)
            case "4":
                print("Starting analysis...")
                run_analysis(system_config=SYSTEM_CONFIG)
            case "5":
                print("Starting setup testing...")
                main_setup_testing(config=CONFIG, system_config=SYSTEM_CONFIG)
            case _:
                print(
                    f"{main_process_selected} is not a valid option, please try a number between [0-5]"
                )
                continue


if __name__ == "__main__":
    run_paradigm()
