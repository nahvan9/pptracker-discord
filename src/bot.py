import logging

from texttable import Texttable
from discordwebhook import Discord


class PPBot:
    def __init__(self, urls: list):
        self.urls = urls

        self.bot = None
        self._dailyUpdate = None
        self._embedColor = None

    def dailyUpdate(self, lastPrice, lastChange, flow, tickers, changes, allocations):
        self.getEmbedColor(lastChange)

        priceSign = self.plusMinus(lastChange)
        flowSign = self.plusMinus(flow)

        self._data, closed = self.createData(tickers, changes, allocations)
        if closed:
            note = "\n*%* Previous Allocation"
        else:
            note = ""
        self._table = self.createTable(self._data)
        self._dailyUpdate = [
            {
                "type": "rich",
                "title": "Meet Kevin's $PP Holdings",
                "description": f"**Last price: ${'{:.2f}'.format(lastPrice)} ({priceSign}{'{:.2f}'.format(lastChange)}%)**",
                "fields": [
                    {
                        "name": "",
                        "value": "```" + self._table.draw() + "```",
                    }
                ],
                "color": self._embedColor,
                "url": "https://www.mketf.com/",
                "footer": {
                    "text": f"Inflow/Outflow: {flowSign}{'{:.2f}'.format(flow)}%{note}"
                },
            }
        ]

        self.sendMutliServer()
        logging.info("All webhooks sent. ")

    def sendMutliServer(self):
        for url in self.urls:
            self.bot = Discord(url=url)
            logging.info(f"Sent Webhook {url}")
            self.bot.post(embeds=self._dailyUpdate)

            self.bot = None

    def getEmbedColor(self, priceChange):
        if priceChange < 0:
            self._embedColor = 0xFF0000
        else:
            self._embedColor = 0x11FF00

    def createTable(self, data):
        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(["t", "a", "a"])
        table.set_cols_align(["l", "r", "r"])
        rows = [["Ticker", "Alloc.", "Changes"]]
        for row in data:
            rows.append(row)

        table.add_rows(rows)

        return table

    def createData(self, tickers, changes, allocations):
        closed = False
        data = []
        size = len(tickers)
        for i in range(size):
            if "Closed❌" in changes[i]:
                closed = True
            data.append([tickers[i], allocations[i], changes[i]])

        return data, closed

    def plusMinus(self, value):
        if value > 0:
            return "+"
        else:
            return ""
