import os.path
import re

import requests

from processors.base_processor import BaseProcessor


class CloudflareProcessor(BaseProcessor):
    TEMPLATE="""#### START CF IPS AUTOMATE ####{}#### END CF IPS AUTOMATE ####"""
    RULE_TEMPLATE = "-A INPUT -s {} -p tcp -m state --state NEW -m tcp -m multiport --dports 80,443 -j ACCEPT"
    local_file = "ips.txt"

    def __init__(self):
        super().__init__()
        if not os.path.isfile(self.local_file):
            open(self.local_file, 'w').close()

    def process(self, config: str) -> str:

        resp = requests.get("https://www.cloudflare.com/ips-v4/", timeout=30)
        if resp.status_code != 200:
            self.logger.error("Cloudflare API returned failed status code {}".format(resp.status_code))
            return config

        remote_ips = self.parse_cf_response(resp.text)
        with open(self.local_file) as f:
            local_ips = self.parse_cf_response(f.read())

        if local_ips == remote_ips:
            self.logger.info("Remote ips is the same. No need update.")
            return config
        self.logger.info("Remote ips changed. Updating...")

        replace_str = self.TEMPLATE.format("\n{}\n")
        regex_map = {
            # added template
            self.TEMPLATE.format(".*"): "",
            # limit line
            "-A INPUT -p tcp -m tcp -m multiport --dports 80,443 -m hashlimit": "\n\n",
            # reject line
            "-A INPUT -j REJECT": "\n\n",
            # very bottom
            "COMMIT": "\n\n",
        }
        find_regex = None
        for regex in regex_map:
            if re.findall(regex, config, flags=re.DOTALL):
                find_regex = regex
                if regex_map[regex]:
                    replace_str = f"{replace_str}{regex_map[regex]}{regex}"
                break

        if not find_regex:
            self.logger.error(f"No regex found. Please check the config file.")
            return config

        # build remote
        list_ips = list(remote_ips)
        list_ips.sort()
        self.logger.info(f"Update ips: {list_ips}")

        replace_str = replace_str.format(
            "\n".join(
                [self.RULE_TEMPLATE.format(x) for x in list_ips]
            ),
        )

        with open(self.local_file, 'w') as f:
            f.write(resp.text)

        return re.sub(find_regex, replace_str, config, flags=re.DOTALL)

    @staticmethod
    def parse_cf_response(cf_response: str) -> set:
        return set([x for x in cf_response.splitlines() if x.strip()])
