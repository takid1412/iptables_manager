import os.path
import re
import sys
import time

import requests

from utils.logger import logger
from utils.pm2 import build_pm2_file

import subprocess

import dotenv
dotenv.load_dotenv()

TEMPLATE="""#### START CF IPS AUTOMATE ####{}#### END CF IPS AUTOMATE ####"""

RULE_TEMPLATE = "-A INPUT -s {} -p tcp -m state --state NEW -m tcp -m multiport --dports 80,443 -j ACCEPT"

def start():
    time_step = 60 * 60
    local_file = "ips.txt"
    iptables_file = os.getenv("IPTABLES_FILE")

    if not os.path.isfile(iptables_file):
        logger.error("Iptables config file '{}' not found".format(iptables_file))
        exit(0)

    if not os.path.isfile(local_file):
        open(local_file, "w").close()

    while True:
        resp = requests.get("https://www.cloudflare.com/ips-v4/", timeout=30)
        if resp.status_code == 200:
            remote_ips = parse_cf_response(resp.text)
            with open(local_file) as f:
                local_ips = parse_cf_response(f.read())
            if local_ips != remote_ips:
                logger.info("Remote ips changed. Updating...")
                with open(iptables_file) as f:
                    current_config = f.read()

                find_regex = TEMPLATE.format(".*")
                replace_str = TEMPLATE.format("\n{}\n")

                if not re.findall(find_regex, current_config, re.DOTALL):
                    logger.info("Not found template format.")
                    ## try finding REJECT Line
                    reject_line = "-A INPUT -j REJECT"
                    if re.findall(reject_line, current_config):
                        find_regex = reject_line
                        replace_str = f"{replace_str}\n\n{reject_line}"
                    else:
                        logger.info(f"Not found {reject_line}. Append before COMMIT")
                        find_regex = "COMMIT"
                        replace_str = f"{replace_str}\n\nCOMMIT"

                # build remote
                list_ips = list(remote_ips)
                list_ips.sort()
                logger.info(f"Update ips: {list_ips}")

                replace_str = replace_str.format(
                    "\n".join(
                        [RULE_TEMPLATE.format(x) for x in list_ips]
                    ),
                )
                new_config = re.sub(find_regex, replace_str, current_config, flags=re.DOTALL)
                with open(iptables_file, "w") as f:
                    f.write(new_config)
                    logger.info(f"New config file written to {iptables_file}")
                with open(local_file, "w") as f:
                    f.write(resp.text)

                #reload config
                try:
                    result = subprocess.run(['systemctl', 'restart', 'iptables'], capture_output=True, text=True, check=True)
                    logger.info(f"Reloaded iptables: {result.stdout}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to reload iptables: {e} - Output: \n{e.stdout}")
                # logger.info(f"Success write new config.")
            else:
                logger.info("Remote not change. Ignore.")


        else:
            logger.error("Failed to fetch remote ips")

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
