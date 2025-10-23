import logging
import sys


logger = logging.getLogger("data_parser")
logger.setLevel(logging.DEBUG) 

# console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# formatting
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)
