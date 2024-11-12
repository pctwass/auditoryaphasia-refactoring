from fire import Fire
from dareplane_utils.default_server.server import DefaultServer

from src.config.config_builder import build_configs
build_configs()

import src.config.system_config as system_config

from src.logging.logger import get_logger
from src.main_processes.main_online import main as main_online
from src.main_processes.main_offline import main as main_offline
from src.main_processes.familiarization import main as main_familiarization
from src.main_processes.analysis import main as main_analysis
from src.main_processes.setup_testing import main as main_setup_testing


def main(port: int = None, ip: str = None, loglevel: int = 10):
    logger = get_logger()
    logger.setLevel(loglevel)

    if ip is None:
        ip = system_config.dareplane_api_ip
    if port is None:
        port = system_config.dareplane_api_port

    pcommand_map = {
        "START ONLINE": main_online,
        "START OFFLINE": main_offline,
        "START FAMILIARIZATION": main_familiarization,
        "START ANALYSIS": main_analysis,
        "START TEST SETUP": main_setup_testing
    }

    server = DefaultServer(
        port, ip=ip, pcommand_map=pcommand_map, name="auditory_aphasia_server"
    )

    # initialize to start the socket
    logger.info(f"initiating audatory aphasia server at {ip}:{port}")
    server.init_server()
    # start processing of the server
    logger.info("listening...")
    server.start_listening()

    return 0


if __name__ == "__main__":
    Fire(main)
