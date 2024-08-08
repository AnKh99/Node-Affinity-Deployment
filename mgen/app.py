import sys
import time
import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if len(sys.argv) != 2:
    logger.error("Usage: app.py <NODE_IP>")
    sys.exit(1)

node_ip = sys.argv[1]

logger.info(f"Starting application with NODE_IP: {node_ip}")

while True:
    try:
        logger.info(f"Request to {node_ip}")
        response = requests.get(f'http://{node_ip}:5000')
        logger.info(f"Response: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
    time.sleep(5)
