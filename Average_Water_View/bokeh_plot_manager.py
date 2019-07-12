from .plot_average_data import PlotAverageData
from PyQt5.QtCore import QThread
from threading import Event
import collections
import pandas as pd
import logging
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
        self.ens_queue = collections.deque()
        self.buff_count = 0

        self.last_4beam_ens = None

        self.bokeh_app_list = []

    def shutdown(self):
        self.thread_alive = False
        self.event.set()

    def set_csv_file(self, file_path):
        """
        Update all the alive dashboards with
        the latest CSV file path.
        :param file_path: Latest CSV file path.
        :return:
        """
        # Update all the dashboards alive
        for app in self.bokeh_app_list:
            app.set_csv_file_path(file_path)

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

    def update_dashboard_from_file(self, file_path):
        """
        Update the dashboard from the CSV file given.
        :param file_path: Path to the CSV file
        :return:
        """
        try:
            # Read in the CSV data
            df = pd.read_csv(file_path)

            # Update all the dashboards alive
            #for app in self.bokeh_app_list:
            #    app.update_dashboard(df)

        except Exception as ex:
            logging.error("Error reading CSV: " + str(ex))

    def update_dashboard(self, avg_df):
        """
        Buffer up the data to display on the dashboard.
        :param avg_df: Dataframe containing the latest data.
        :return:
        """
        # Add data to the queue
        self.data_queue.append(avg_df)

        self.buff_count += 1

        #if self.buff_count >= int(self.rti_config.config['PLOT']['BUFF_SIZE']):
        # Wakeup the thread
        self.event.set()

    def plot_ens(self, ens):
        """
        Buffer up the ensemble data and wakeup the thread.
        :param ens:
        :return:
        """
        # Add data to the queue
        self.ens_queue.append(ens)

        # Wakeup the thread
        self.event.set()

    def run(self):
        """
        Look for a group of 4 beam and vertical beam
        It is assumed tha the vertical beam will come after
        the 4 beam data.  So look for vertical beam data and
        group with last 4 beam data.
        :return:
        """

        while self.thread_alive:

            # Wait to be woken up
            self.event.wait()

            # Process any data in the df buffer
            # This buffer is only used if averaging is done
            if len(self.data_queue) > 0:
                self.process_df_buffer()

            # Process any data in the ensemble buffer
            # This buffer is only used if no averaging is done
            if len(self.ens_queue) > 0:
                self.process_ens_buff()

            # Clear automatically
            self.event.clear()

    def process_ens_buff(self):
        """
        Process the ensemble buffer.  If no averaging is done,
        then ensembles will be passed here.  Process all the ensembles
        in the buffer.
        :return:
        """

        # Processed all queued data
        while len(self.ens_queue) > 0:

            # Remove the dataframe from the queue
            ens = self.ens_queue.popleft()

            if ens:
                if ens.IsEnsembleData:
                    # Check if a 3 or 4 Beam ensemble
                    if ens.EnsembleData.NumBeams >= 3:
                        self.last_4beam_ens = ens
                    # Check if it is a vertical beam ensemble
                    # If vertical beam, then process the data
                    elif ens.EnsembleData.NumBeams == 1:
                        # If a 4 Beam has been found, then group them into a list
                        if self.last_4beam_ens:
                            # Pass the data to the plot to be processed
                            for app in self.bokeh_app_list:
                                app.process_ens_group(fourbeam_ens=self.last_4beam_ens, vert_ens=ens)

    def process_df_buffer(self):
        """
        This will check if the df queue has any data.
        Then pop the data out of the and add the data to the display.
        Update all the created dashboards in the list.
        :return:
        """
        #start_loop = time.process_time()
        while len(self.data_queue) > 0:

            # Remove the dataframe from the queue
            avg_df = self.data_queue.popleft()

            for app in self.bokeh_app_list:
                app.update_dashboard(avg_df)

        #print("Process DF buffer: " + str(time.process_time() - start_loop))

