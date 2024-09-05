from fire import Fire

import dependency_resolver
import config.temp_new_conf as temp_new_config

from dareplane_utils.default_server.server import DefaultServer
from dareplane_utils.logging.logger import get_logger

from main_online import main as main_online
from main_offline import main as main_offline
# from familiarization import main as main_familiarization
from analysis import main as main_analysis
from setup_testing import main as main_setup_testing


def main(port: int = None, ip: str = None, loglevel: int = 10):
    logger = get_logger("AuditoryAphasia")
    logger.setLevel(loglevel)

    if ip is None:
        ip = temp_new_config.api_ip
    if port is None:
        port = temp_new_config.api_port

    pcommand_map = {
        "START ONLINE": main_online,
        "START OFFLINE": main_offline,
        # "START FAMILIARIZATION": main_familiarization,
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
