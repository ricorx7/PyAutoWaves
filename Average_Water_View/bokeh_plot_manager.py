from .plot_average_data import PlotAverageData
from PyQt5.QtCore import QThread
from threading import Event
import collections
import pandas as pd
import logging
import time
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn


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
        self.data_queue = collections.deque(maxlen=int(self.rti_config.config['PLOT']['MAX_POINTS']*2))
        self.ens_queue = collections.deque(maxlen=int(self.rti_config.config['PLOT']['MAX_POINTS'])*2)
        self.buff_count = 0

        self.last_4beam_ens = None
        self.last_4beam_awc = None

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

    def update_dashboard_awc(self, awc):
        """
        Buffer up the data to display on the dashboard.
        :param awc: Latest AverageWaterColumn data to plot.
        :return:
        """
        # Add data to the queue
        self.data_queue.append(awc)

        self.buff_count += 1

        # Wakeup the thread
        self.event.set()

    def update_dashboard_ens(self, ens):
        """
        Buffer up the ensemble data and wakeup the thread.
        :param ens: Latest ensemble to plot.
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

            # Process any data in the AverageWaterColumn buffer
            # This buffer is only used if averaging is done
            if len(self.data_queue) > 0:
                self.process_awc_buffer()

            # Process any data in the ensemble buffer
            # This buffer is only used if no averaging is done
            if len(self.ens_queue) > 0:
                self.process_ens_buff()

            # Clear automatically
            self.event.clear()

    def process_ens_buff(self):
        """
        Check the buffer for the latest data.  Look for a 4 beam and vertical beam
        ensemble.  When both are found, then pass the data to be plotted.

        It is assumed that the data will go in the order 4 beam then vertical beam.
        So store the 4 beam data.  When vertical beam data is found, then use the
        stored 4 beam data with the vertical beam data as a combination to plot the data.
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
                        if not self.rti_config.config.getboolean('Waves', '4b_vert_pair'):
                            # Pass only the 4 beam data to be plotted
                            for app in self.bokeh_app_list:
                                app.process_ens_group(fourbeam_ens=self.ens, vert_ens=None)
                        else:
                            # Buffer the last 4 Beam ENS
                            self.last_4beam_ens = ens
                    # Check if it is a vertical beam ensemble
                    # If vertical beam, then process the data
                    elif ens.EnsembleData.NumBeams == 1:
                        # If a 4 Beam has been found, then group them into a list
                        if self.last_4beam_ens:
                            # Pass the data to the plot to be processed
                            for app in self.bokeh_app_list:
                                app.process_ens_group(fourbeam_ens=self.last_4beam_ens, vert_ens=ens)

    def process_awc_buffer(self):
        """
        Check the buffer for the latest data.  Look for a 4 beam and vertical beam
        AverageWaterColumn.  When both are found, then pass the data to be plotted.

        It is assumed that the data will go in the order 4 beam then vertical beam.
        So store the 4 beam data.  When vertical beam data is found, then use the
        stored 4 beam data with the vertical beam data as a combination to plot the data.
        :return:
        """
        #start_loop = time.process_time()
        while len(self.data_queue) > 0:

            # Remove the AverageWaterColumn from the queue
            awc = self.data_queue.popleft()

            if awc:
                # Check if a 3 or 4 Beam ensemble
                if awc[AverageWaterColumn.INDEX_NUM_BEAM] >= 3:
                    if not self.rti_config.config.getboolean('Waves', '4b_vert_pair'):
                        # Pass the data to the plot to be processed
                        for app in self.bokeh_app_list:
                            app.process_awc_group(fourbeam_awc=awc, vert_awc=None)
                    else:
                        # Buffer the last 4 Beam AWC
                        self.last_4beam_awc = awc
                # Check if it is a vertical beam ensemble
                # If vertical beam, then process the data
                elif awc[AverageWaterColumn.INDEX_NUM_BEAM] == 1:
                    # If a 4 Beam has been found, then group them into a list
                    if self.last_4beam_awc:
                        # Pass the data to the plot to be processed
                        for app in self.bokeh_app_list:
                            app.process_awc_group(fourbeam_awc=self.last_4beam_awc, vert_awc=awc)

        #print("Process DF buffer: " + str(time.process_time() - start_loop))

