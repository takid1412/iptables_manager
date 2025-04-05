import json
import os
import sys

from utils.logger import create_logger
logger = create_logger("PM2")

def build_pm2_file():
    obj = {
        "apps": []
    }
    cwd = os.getcwd()
    python_bin = os.getenv("PYTHON_BIN")
    log_dir = os.getenv("LOG_DIR")

    main_file = os.path.basename(sys.argv[0])
    log_file = f"{log_dir}/{os.path.splitext(main_file)[0]}.log"
    obj['apps'].append({
        "name": f"Iptables Manager",
        "script": main_file,
        "args": "start",
        "merge_logs": True,
        "cwd": cwd,
        "out_file": log_file,
        "error_file": log_file,
        "interpreter": python_bin,
        "interpreter_args": "-u"
    })

    out_file = 'pm2_generated.json'
    with open(out_file, 'w') as f:
        f.truncate()
        f.write(json.dumps(obj, indent=4))
        f.close()
    logger.info("Generated file at {}".format(out_file))
