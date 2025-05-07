import threading
from Price import RobotPrice
from Plotter import SubplotAnimation
from TradeMonitor import TradeMonitor

def create_MonitorPrice(instrument,days,timeframe):
    robot = RobotPrice(days,instrument,timeframe)
    robot.setMonitorPriceData()
    
def create_trademonitor(instrument,timeframe,timeframe_sup,timeframe_sup2,days):
    trade = TradeMonitor(instrument,timeframe,timeframe_sup,timeframe_sup2,days)
    trade.startMonitor()

def create_plotter(instrument,timeframe,timeframe_sup,timeframe_sup2,days):
    ani = SubplotAnimation(instrument=instrument, timeframe=timeframe,timeframe_sup=timeframe_sup,timeframe_sup2=timeframe_sup2,days=days)
    ani.plt.show()
    

if __name__ == "__main__":
        instrument="EUR/USD"
        timeframe = "m1"
        timeframe_sup = "m15"
        timeframe_sup2 = "m30"
        days = 7

        t1 = threading.Thread(target=create_MonitorPrice, name="timeFrame"+timeframe+instrument, args=(instrument,days,timeframe))
        t2 = threading.Thread(target=create_MonitorPrice, name="timeFrame"+timeframe_sup+instrument, args=(instrument,days,timeframe_sup))
        t3 = threading.Thread(target=create_MonitorPrice, name="timeFrame"+timeframe_sup2+instrument, args=(instrument,days,timeframe_sup2))
        
        t1.start(), t2.start(), t3.start()

        monitor = threading.Thread(target=create_trademonitor, name="monitor"+instrument, args=(instrument,timeframe,timeframe_sup,timeframe_sup2,days))
        monitor.start()

        ploter = threading.Thread(target=create_plotter, name="ploter"+instrument, args=(instrument,timeframe, timeframe_sup,timeframe_sup2,days))
        ploter.start()

