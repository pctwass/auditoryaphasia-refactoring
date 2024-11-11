import src.config.config_builder as config_builder
config_builder.build_configs()

import src.config.config as config
import src.config.system_config as system_config
import src.config.classifier_config as classifier_config
from src.main_processes.main_online import main as main_online
from src.main_processes.main_offline import main as main_offline
from src.main_processes.familiarization import main as main_familiarization
from src.main_processes.analysis import main as main_analysis
from src.main_processes.setup_testing import main as main_setup_testing


def main():
    print('--------------------------------------------------------')
    print('1: AMUSE online')
    print('2: AMUSE offline')
    print('3: Familarization')
    print('4: Analysis')
    print('5: Setup test')
    print('0: Quit')
    print('--------------------------------------------------------')
    
    while True:
        main_process_selected = int(input())

        match main_process_selected:
            case 0: return
            case 1: 
                print("Starting AMUSE online...")
                main_online()
            case 2: 
                print("Starting AMUSE offline...")
                main_offline()
            case 3: 
                print("Starting familarization...")
                main_familiarization()
            case 4: 
                print("Starting analysis...")
                main_analysis()
            case 5: 
                print("Starting setup testing...")
                main_setup_testing()
            case _: 
                print(f"{main_process_selected} is not a valid option, please try a number between [0-5]")
                continue


if __name__ == '__main__':
    main()