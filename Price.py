import pandas as pd


from datetime import datetime
from pytz import timezone 
import numpy as np
import pandas as pd
from scipy import signal
import datetime as dt
from ConnectionFxcm import RobotConnection
import time

class RobotPrice: 
        def __init__(self):  
                self.pricedata = None            

        def __init__(self, days, instrument, timeframe):
                self.instrument = instrument
                self.timeframe = timeframe
                self.pricedata = None
                self.days = days
                self.robotconnection = RobotConnection()
                self.connection = self.robotconnection.getConnection()

        def __del__(self):
                print('Object gets destroyed')
                self.connection.logout()

        def savePriceDataFile(self,pricedata):
                fileName = self.instrument.replace("/", "_") + "_" + self.timeframe + ".csv"                
                pricedata.to_csv(fileName)
        
        def savePriceDataFileConsolidated(self, pricedata, timeframe, timeframe_sup):
                fileName = self.instrument.replace("/", "_") + "_" + timeframe + "_" + timeframe_sup + ".csv"   
                pricedata.to_csv(fileName)

        def readData(self, instrument, timeframe):
                return pd.read_csv(instrument.replace("/", "_") + '_' + timeframe + '.csv')
        
        @staticmethod
        def readPriceDataFileConsolidated(self, timeframe, timeframe_sup):
                return pd.read_csv(self.instrument.replace("/", "_") + '_' + timeframe + "_" + timeframe_sup + ".csv")

        def getPricesConsolidated(self, instrument, timeframe, timeframe_sup,timeframe_sup2):
                pricedata_inf = self.readData(instrument, timeframe)
                pricedata_sup = self.readData(instrument, timeframe_sup)        
                pricedata_sup2 = self.readData(instrument, timeframe_sup2)
                pricedata = pd.concat([pricedata_sup2 , pricedata_sup, pricedata_inf], ignore_index=True)
                pricedata = pricedata.sort_values(by='date').reset_index(drop=True)
                return pricedata     
        
        def setIndicators(self, df):
                df['value1'] = 1
                # Find local peaks
                df['peaks_min'] = df.iloc[signal.argrelextrema(df['bidclose'].values,np.less,order=30)[0]]['value1']
                df['peaks_max'] = df.iloc[signal.argrelextrema(df['bidclose'].values,np.greater,order=30)[0]]['value1']
                df['ema'] = df['bidclose'].ewm(span=10).mean()
                df['ema_slow'] = df['bidclose'].ewm(span=100).mean()

                # Determine RSI window based on timeframe
                if self.timeframe in ["m1", "m5"]:
                        rsi_window = 7  # Shorter window for lower timeframes
                elif self.timeframe in ["m15", "m30"]:
                        rsi_window = 14  # Standard window for medium timeframes
                elif self.timeframe in ["H1", "H4"]:
                        rsi_window = 21  # Longer window for higher timeframes
                else:
                        rsi_window = 14  # Default fallback

                # Add RSI indicator with dynamic window
                delta = df['bidclose'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_window).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_window).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))

                # ***********************************************************
                # * Strategy SELL
                # ***********************************************************
                df['sell'] = 0
                operationActive = False
                for index, row in df.iterrows():
                        # if not operationActive and df.loc[index, 'peaks_max'] == 1 and df.loc[index, 'ema'] < df.loc[index, 'ema_slow'] and df.loc[index, 'rsi'] > 70:
                        # if not operationActive and df.loc[index, 'peaks_max'] == 1 and df.loc[index, 'ema'] < df.loc[index, 'ema_slow']:
                        if not operationActive and df.loc[index, 'peaks_max'] == 1 and df.loc[index, 'rsi'] > 70:
                                operationActive = True
                                df.loc[index, 'sell'] = 1  # Open sell operation
                        elif operationActive and df.loc[index, 'peaks_min'] == 1:
                                df.loc[index, 'sell'] = -1  # Close sell operation
                                operationActive = False

                # ***********************************************************
                # * Strategy BUY
                # ***********************************************************
                df['buy'] = 0
                operationActive = False
                for index, row in df.iterrows():
                        # if not operationActive and df.loc[index, 'peaks_min'] == 1 and df.loc[index, 'ema'] > df.loc[index, 'ema_slow'] and df.loc[index, 'rsi'] < 30:
                        # if not operationActive and df.loc[index, 'peaks_min'] == 1 and df.loc[index, 'ema'] > df.loc[index, 'ema_slow']:
                        if not operationActive and df.loc[index, 'peaks_min'] == 1 and df.loc[index, 'rsi'] < 30:
                                  
                                operationActive = True
                                df.loc[index, 'buy'] = 1  # Open buy operation
                        elif operationActive and df.loc[index, 'peaks_max'] == 1:
                                df.loc[index, 'buy'] = -1  # Close buy operation
                                operationActive = False

                return df
        
        def getPriceData(self, instrument, timeframe, days, connection):
                europe_London_datetime = datetime.now( timezone('Europe/London') )
                date_from =  europe_London_datetime - dt.timedelta(days=days)
                date_to = europe_London_datetime
                try:
                        
                        history = connection.get_history(instrument, timeframe, date_from, date_to)
                        current_unit, _ = connection.parse_timeframe(timeframe)
                        print("Price Data Received..." + str(current_unit) + " " + str(timeframe) + " " + str(instrument) + " " + str(europe_London_datetime))

                        pricedata = pd.DataFrame(history, columns = ["Date", "BidOpen", "BidHigh", "BidLow", "BidClose", "Volume"])

                        d =    {'date': pricedata['Date'],
                                'bidhigh': pricedata['BidHigh'],
                                'bidlow': pricedata['BidLow'],
                                'bidclose': pricedata['BidClose'],
                                'bidopen': pricedata['BidOpen'], 
                                'tickqty': pricedata['Volume']         
                                }
                        
                        df = pd.DataFrame(data=d)
                        df['timeframe'] = timeframe
                        df['date'] = df['date'].astype(str).str.replace('-', '').str.replace(':', '').str.replace(' ', '').str[:-2]
                        df['date']= df['date'].apply(lambda x: int(x))
                        self.pricedata = self.setIndicators(df)
                        self.savePriceDataFile(self.pricedata)
                        return self.pricedata
                except Exception as e:
                        print("Exception: " + str(e))

        def setMonitorPriceData(self):
                self.getPriceData(instrument=self.instrument, timeframe=self.timeframe, days=self.days,connection=self.connection)
                while True:
                        currenttime = dt.datetime.now()  
                        if self.timeframe == "m1" and currenttime.second == 0:
                                self.getPriceData(instrument=self.instrument, timeframe=self.timeframe, days=self.days,connection=self.connection)
                                time.sleep(1)                    
                        elif self.timeframe == "m5" and currenttime.second == 0 and currenttime.minute % 5 == 0:
                                self.getPriceData(instrument=self.instrument, timeframe=self.timeframe, days=self.days,connection=self.connection)
                                time.sleep(240)
                        elif self.timeframe == "m15" and currenttime.second == 0 and currenttime.minute % 15 == 0:
                                self.getPriceData(instrument=self.instrument, timeframe=self.timeframe, days=self.days,connection=self.connection)
                                time.sleep(840)
                        elif self.timeframe == "m30" and currenttime.second == 0 and currenttime.minute % 30 == 0:
                                self.getPriceData(instrument=self.instrument, timeframe=self.timeframe, days=self.days,connection=self.connection)
                                time.sleep(1740)
                        elif self.timeframe == "H1" and currenttime.second == 0 and currenttime.minute == 0:
                                self.getPriceData(instrument=self.instrument, timeframe=self.timeframe, days=self.days,connection=self.connection)
                                time.sleep(3540)
                        time.sleep(1)