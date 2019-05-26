from .plot_average_data import PlotAverageData
from PyQt5.QtCore import QThread
from threading import Event
import collections
import time


class BokehPlotManager(QThread):
    """
    Create a new bokeh app for each instance that is opened.
    """

    def __init__(self, rti_config):
        QThread.__init__(self)
        """
        Initialize the object.
        :param rti_config: RTI Config.
        """
        self.rti_config = rti_config

        # Threading
        self.thread_alive = True
        self.event = Event()
        self.data_queue = collections.deque()

        self.bokeh_app_list = []

    def shutdown(self):
        self.thread_alive = False
        self.event.set()

    def setup_bokeh_server(self, doc):
        """
        Create a Bokeh App for the bokeh server.
        Each webpage open needs its own instance of PlotAverageData.
        :param doc: Doc to load for the webpage
        :return:
        """

        # Create a Plot Average Data object
        pad = PlotAverageData(self.rti_config)

        # Add the PlotAverageData to the list
        self.bokeh_app_list.append(pad)

        # Initialize the bokeh server with the plots
        pad.setup_bokeh_server(doc)

    def update_dashboard(self, avg_df):
        """
        Buffer up the data to display on the dashboard.
        :param avg_df: Dataframe containing the latest data.
        :return:
        """
        # Add data to the queue
        self.data_queue.append(avg_df)

        # Wakeup the thread
        self.event.set()

    def run(self):
        """
        Running thread.  This will check if the queue has any data.
        Then pop the data out of the and add the data to the display.
        Update all the created dashboards in the list.
        :return:
        """

        while self.thread_alive:

            # Wait to be woken up
            self.event.wait()

            #start_loop = time.process_time()
            while len(self.data_queue) > 0:

                # Remove the dataframe from the queue
                avg_df = self.data_queue.popleft()

                #start_dash = time.process_time()
                for app in self.bokeh_app_list:
                    app.update_dashboard(avg_df)
                #print("Dash loop: " + str(time.process_time() - start_dash))

            #print("Main loop: " + str(time.process_time() - start_loop))

            # Clear automatically
            self.event.clear()
