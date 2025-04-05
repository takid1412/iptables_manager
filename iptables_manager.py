import os.path
import re
import sys
import time

import requests

from processors.cloudflare_processor import CloudflareProcessor
from utils.logger import create_logger
from utils.pm2 import build_pm2_file

import subprocess

import dotenv
dotenv.load_dotenv()

logger = create_logger("main")

def start():
    time_step = 60 * 60
    iptables_file = os.getenv("IPTABLES_FILE")

    if not os.path.isfile(iptables_file):
        logger.error("Iptables config file '{}' not found".format(iptables_file))
        exit(0)

    while True:
        with open(iptables_file) as f:
            config = f.read()
        new_config = config
        processors = [
            CloudflareProcessor()
        ]
        for processor in processors:
            new_config = processor.process(config)

        if new_config != config:
            with open(iptables_file, "w") as f:
                f.write(new_config)
                logger.info(f"New config file written to {iptables_file}")

            try:
                result = subprocess.run(['systemctl', 'restart', 'iptables'], capture_output=True, text=True, check=True)
                logger.info(f"Reloaded iptables: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to reload iptables: {e} - Output: \n{e.stdout}")
        else:
            logger.info("Config not change")

        logger.info(f"End round. Next in approx {int(time_step/60)}min")
        time.sleep(time_step)

def parse_cf_response(cf_response: str) -> set:
    return set([x for x in cf_response.splitlines() if x.strip()])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        act = sys.argv[1]

        act_map = {
            'pm2': build_pm2_file,
            'start': start,
        }
        if act in act_map:
            act_map[act]()
        else:
            logger.error("Invalid Action. Available: {}".format(", ".join(act_map.keys())))

    else:
        logger.error("Need Action Param")
