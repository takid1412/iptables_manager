import logging
from pathlib import Path

LOG_LEVEL = logging.DEBUG

# create auxiliary variables
loggerName = Path(__file__).stem

# create logging formatter
logFormatter = logging.Formatter(fmt='%(asctime)s :: %(name)s :: %(levelname)-8s :: %(message)s',
                                 datefmt='%d-%m-%Y %H:%M:%S')

# create logger
logger = logging.getLogger(loggerName)
logger.setLevel(LOG_LEVEL)

# create console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(LOG_LEVEL)
consoleHandler.setFormatter(logFormatter)

# Add console handler to logger
logger.addHandler(consoleHandler)
