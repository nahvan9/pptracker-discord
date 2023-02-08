import os
import logging
import sqlite3
import requests

import yfinance as yf
import pandas as pd

from datetime import datetime


class MKPP():
    def __init__(self, dbPath, filesPath, discordbot):
        self.url='https://www.mketf.com/wp-content/fund_files/files/TidalETF_Services.40ZZ.K3_Holdings_PP.csv'
        self.db = dbPath

        self.files = filesPath
        self.conn = sqlite3.connect(os.path.join(dbPath, 'database.db'))
        self.bot = discordbot
        self.pp = yf.Ticker("PP")

        self.tickers = []
        self.changes = []
        self.alloc = []
        self.lastPrice = None
        self.priceChange = None
        self.mcap = None

        self.initdb()


    # Gets $PP price change at close compared to previous close price
    def getPriceChange(self):
        prevClose = self.pp.fast_info['regularMarketPreviousClose']
        self.lastPrice = round(self.pp.fast_info['last_price'], 2)
        self.priceChange = round(self.lastPrice-prevClose, 2)
        # self.mcap = self.pp.fast_info['marketCap']

    # Initiates sqlite db
    # https://github.com/rajsinghtech/pptracker 
    def initdb(self):
        cursor = self.conn.cursor()
        query = 'CREATE VIEW if not EXISTS latest as SELECT * from holdings WHERE Date = (SELECT DISTINCT date from holdings ORDER BY date DESC LIMIT 1 OFFSET 0)'
        cursor.execute(query)
        query = 'CREATE VIEW if not EXISTS dayBefore as SELECT * from holdings WHERE Date = (SELECT DISTINCT date from holdings ORDER BY date DESC LIMIT 1 OFFSET 1)'
        cursor.execute(query)
        query = '''
        CREATE VIEW if not EXISTS change as SELECT stockticker, 
        (latest.Shares - dayBefore.Shares) as change, 
        (latest.Shares - 0) as latest, 
        (latest.Weightings - 0) as latestW, 
        (dayBefore.Shares - 0) as dayBefore,
        (dayBefore.Weightings - 0) as dayBeforeW,
        (latest.SharesOutstanding - 0) as latestSO,
        (dayBefore.SharesOutstanding - 0) as dayBeforeSO,
        (latest.SharesOutstanding - dayBefore.SharesOutstanding) as shChange
        from latest left JOIN dayBefore using (stockticker)
        union
        SELECT stockticker, 
        (latest.Shares - dayBefore.Shares) as change, 
        (latest.Shares - 0) as latest, 
        (latest.Weightings - 0) as latestW, 
        (dayBefore.Shares - 0) as dayBefore,
        (dayBefore.Weightings - 0) as dayBeforeW,
        (latest.SharesOutstanding - 0) as latestSO,
        (dayBefore.SharesOutstanding - 0) as dayBeforeSO,
        (latest.SharesOutstanding - dayBefore.SharesOutstanding) as shChange
        from dayBefore left JOIN latest using (stockticker)
        '''
        cursor.execute(query)
        self.conn.commit()
        for filename in os.listdir(self.files):
            df = pd.read_csv(os.path.join(self.files, filename))
            self.importPP(df)

    # Append csv files to db
    # https://github.com/rajsinghtech/pptracker 
    def importPP(self, df):
        df.to_sql('holdings', self.conn, if_exists='append', index=False)
        cursor = self.conn.cursor()
        cursor.execute("""DELETE FROM holdings
        WHERE EXISTS (
        SELECT 1 FROM holdings p2 
        WHERE holdings.Date = p2.Date
        AND holdings.StockTicker = p2.StockTicker
        AND holdings.rowid > p2.rowid
        );
        """)
        self.conn.commit()
    
    # Load csv files
    # https://github.com/rajsinghtech/pptracker 
    def getPP(self):
        response = requests.get(self.url)
        temp = os.path.join(self.db, 'temp.csv')
        with open(temp, 'w') as f:
            f.write(response.text)
        df = pd.read_csv(temp)
        df['Date'] = df['Date'].apply(lambda x: datetime.strptime(x, "%m/%d/%Y").strftime("%Y-%m-%d"))
        today = df.iloc[0, df.columns.get_loc('Date')]
        df.to_csv(os.path.join(self.files, today + '.csv'), index=False)

        return df
    
    # https://github.com/rajsinghtech/pptracker 
    def p2f(self, x):
        return float(x.strip('%'))/100
    
    # https://github.com/rajsinghtech/pptracker 
    def checkDate(self):
        cursor = self.conn.cursor()
        query = 'SELECT DISTINCT date from holdings ORDER BY date DESC LIMIT 1'
        cursor.execute(query)
        x = cursor.fetchall()
        self.conn.commit()
        return x[0][0]

    # https://github.com/rajsinghtech/pptracker 
    def getChange(self):
        query = '''
        SELECT * FROM change
        ORDER BY
        latestW DESC;
        '''
        df = pd.read_sql(query, self.conn)
        return(df)

    # https://github.com/rajsinghtech/pptracker 
    def writeDate(self, text):
        with open(os.path.join(self.db,'date.txt'), 'w') as f:
            f.write(text)

    # https://github.com/rajsinghtech/pptracker 
    def readDate(self):
        with open(os.path.join(self.db,'date.txt'), 'r') as f:
            text = f.read()
        return text

    def getUpdates(self):
            stocks = self.getChange()
            row = stocks.iloc[0]
            inflow = row['shChange']/row['dayBeforeSO']

            tickers = []
            changes = []
            allocations = []

            for index, stock in stocks.iterrows():
                # Open or Closed position
                if stock['change'] != stock['change']:
                    if stock['latest'] != stock['latest']:
                        tickers.append('$'+stock['StockTicker'])
                        changes.append("Closed❌")
                        allocations.append(f"*{stock['dayBeforeW']}%*")
                    else:
                        tickers.append('$'+stock['StockTicker'])
                        changes.append("Opened✅")
                        allocations.append(f"{stock['latestW']}%")

                # Change, accounted for inflow/outflows
                elif stock['change']:
                    tickers.append('$'+stock['StockTicker'])
                    change = round(((stock['change']/stock['dayBefore'])-inflow)*100, 2)

                    if abs(change) <= 0.05:
                        changes.append('---')
                    elif change > 0.05:
                        changes.append(f"+{change}%🟢")
                    elif change < -0.05:
                        changes.append(f"{change}%🔴")

                    allocations.append(f"{stock['latestW']}%")

                # If no changes
                else:
                    tickers.append('$'+stock['StockTicker'])
                    changes.append('---')
                    allocations.append(f"{stock['latestW']}%")

            return tickers, changes, allocations, inflow
    

    def updateBot(self, tickers, changes, allocations, inflow):
        if inflow > 0:
            strInflow = f'+{round(inflow * 100, 2)}'
        else:
            strInflow = f'{round(inflow * 100, 2)}'

        self.bot.dailyUpdate(
            lastPrice=self.lastPrice, 
            lastChange=self.priceChange, 
            flow=strInflow,
            tickers=tickers, 
            changes=changes,
            allocations=allocations,
        )

    def run(self):
        try: 
            logging.info("Checking Holdings")
            df = self.getPP()
            self.importPP(df)
            currentDate = self.checkDate()
            prevDate = self.readDate()
            if  currentDate != prevDate:
                self.writeDate(currentDate)

                self.getPriceChange()

                tickers, changes, allocations, inflow = self.getUpdates()
                self.updateBot(
                    tickers=tickers,
                    changes=changes,
                    allocations=allocations,
                    inflow=inflow
                )
        except Exception as e:
            logging.critical("pp Error")
            logging.critical(e)
        
    def rundemo(self):
        """Demo data"""
        tickers, changes, allocations, inflow = self.getUpdates()
        
        self.bot.dailyUpdate(
            lastPrice=42.69, 
            lastChange=-0.69, 
            flow='+4.20',
            tickers=tickers, 
            changes=changes,
            allocations=allocations,
        )