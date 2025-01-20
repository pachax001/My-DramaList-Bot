# log_config.py
import logging
from logging.handlers import RotatingFileHandler
import sys
# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
file_handler = RotatingFileHandler(
    "log.txt",
    maxBytes=5*1024*1024,  # 5 MB
    backupCount=0,  # Keep up to 0 backup log files
    encoding="utf-8"
)
stream_handler = logging.StreamHandler(sys.stdout)

# Create formatters and add them to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(name)s - %(levelname)s - %(message)s')  # Include filename and line number
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)