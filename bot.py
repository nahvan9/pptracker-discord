import logging

# from datetime import datetime
# from datetime import timedelta

from texttable import Texttable
from discordwebhook import Discord

class PPBot():
    def __init__(self, url, utc):
        self.bot = Discord(url=url)
        self.time_offset = int(utc)
        self._dailyUpdate = None
        self._embedColor = None


    def dailyUpdate(self, lastPrice, lastChange, flow, tickers, changes, allocations):
        self.getEmbedColor(lastChange)
        if lastChange > 0: 
            sign = '+'
        else:
            sign = ''
            
        self._data = self.createData(tickers, changes, allocations)
        self._table = self.createTable(self._data)
        # time = self.getTime()
        self._dailyUpdate = [{
            # "timestamp": time,
            "type": "rich",
            "title": "Meet Kevin\'s $PP Holdings",
            "description": f"**Last price: ${lastPrice} ({sign}{lastChange}%)**",
            "fields": [
                {
                    "name": "",
                    "value": "```"+self._table.draw()+"```",
                }
            ],
            "color": self._embedColor,
            "url": "https://www.mketf.com/",
            "footer": {
                "text": f"Inflow/Outflow: {flow}%"
            }
        }]
        
        self.bot.post(embeds=self._dailyUpdate)
        logging.info("Embed sent. ")

    def getEmbedColor(self, priceChange):
        if priceChange < 0:
            self._embedColor = 0xff0000
        else:
            self._embedColor = 0x11ff00

    def createTable(self, data):
        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 'a', 'a'])
        table.set_cols_align(["l", "r", "r"])
        rows = [["Ticker", "Alloc.", "Changes"]]
        for row in data:
            rows.append(row)
        
        table.add_rows(rows)

        return table

    def createData(self, tickers, changes, allocations):
        data = []
        size = len(tickers)
        for i in range(size):
            data.append([tickers[i], allocations[i], changes[i]])

        return data
    
    # def getTime(self):
    #     return str(datetime.now()+timedelta(hours=self.time_offset))