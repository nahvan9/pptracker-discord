import os
import time
import logging
import json

from dotenv import load_dotenv

from src.pp import MKPP
from src.bot import PPBot

load_dotenv()


SLEEP = int(os.getenv("SLEEP"))

DB_PATH = os.path.join(os.getcwd(), "db")
FILES = os.path.join(os.getcwd(), "files")
LOGS = os.path.join(os.getcwd(), "logs")
JSON = os.path.join(os.getcwd(), "json")
URL_PATHS = os.path.join(JSON, "webhooks.json")

paths = [DB_PATH, FILES, LOGS, JSON]

for path in paths:
    if not os.path.exists(path):
        os.mkdir(path)

if os.path.exists(URL_PATHS):
    with open(URL_PATHS, "r") as j:
        URLS = json.load(j)


logging.basicConfig(
    filename=os.path.join(LOGS, "main.log"),
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def cleanFiles():
    """Removes csv files older than 8 days"""

    logging.info("Deleting old csv files...")
    now = time.time()
    files = [os.path.join(FILES, filename) for filename in os.listdir(FILES)]
    fd = 0
    for filename in files:
        if (now - os.stat(filename).st_mtime) > 691200:
            fd += 1
            os.remove(filename)
            logging.info(f"Removed {filename}")
    if fd == 0:
        logging.info("No files deleted. ")


if __name__ == "__main__":
    bot = PPBot(urls=URLS)
    pp = MKPP(DB_PATH, FILES, discordbot=bot)

    while True:
        cleanFiles()
        pp.run()
        logging.info("Sleeping")
        time.sleep(SLEEP)

    # # Demo
    # pp.rundemo()
