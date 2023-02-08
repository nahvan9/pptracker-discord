import os
import time
import logging

from dotenv import load_dotenv

from pp import MKPP
from bot import PPBot

load_dotenv()

WEBHOOKURL = os.getenv('WEBHOOK')
SLEEP = int(os.getenv('SLEEP'))
UTC_OFFSET = time.timezone/3600

DB_PATH = os.path.join(os.getcwd(), 'db')
FILES = os.path.join(os.getcwd(), 'files')
LOGS = os.path.join(os.getcwd(), 'logs')
date = os.path.join(DB_PATH, 'date.txt')

paths = [DB_PATH, FILES, LOGS, date]

for path in paths:
    if not os.path.exists(path):
        os.mkdir(path)

logging.basicConfig(filename=os.path.join(LOGS, 'main.log'), format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)


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

    bot = PPBot(url=WEBHOOKURL, utc=UTC_OFFSET)
    pp = MKPP(DB_PATH, FILES, discordbot=bot)
    
    while True:
        cleanFiles()
        pp.run()
        logging.info("Sleeping")
        time.sleep(SLEEP)
