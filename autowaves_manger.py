import logging
import math
from collections import deque
from threading import Thread, Event
import threading
from rti_python.Codecs.AdcpCodec import AdcpCodec
from rti_python.Codecs.WaveForceCodec import WaveForceCodec
from rti_python.Utilities.config import RtiConfig
from rti_python.Codecs.BinaryCodec import BinaryCodec
import time


class AutoWavesManager:
    """
    Montitor all the VM.  Pass any events to the VM.
    Pass data from the serial port to the ADCP codec.
    """
    def __init__(self, parent, rti_config, terminal_vm, setup_vm, monitor_vm, avg_water_vm):
        """
        Initialize the manager.
        :param parent: Parent.  Main window.
        :param rti_config: RTI Config file object.
        :param terminal_vm: Terminal VM.
        :param setup_vm: Setup VM.
        :param monitor_vm: Monitor VM.
        :param avg_water_vm: Average Water Column VM.
        """
        self.parent = parent
        self.terminal_vm = terminal_vm
        self.setup_vm = setup_vm
        self.monitor_vm = monitor_vm
        self.avg_water_vm = avg_water_vm

        self.logger = logging.getLogger('root')

        self.rti_config = rti_config

        self.adcp_codec = AdcpCodec()

        self.avg_ens_count = 0

        # Ensemble processing thread
        self.ens_thread_alive = True
        self.ens_queue = deque()
        self.ens_thread_event = Event()
        self.ens_thread = Thread(name="autowaves_mgr", target=self.ens_thread_run)
        self.ens_thread.start()

        # Verify the selected bin is not disabled
        selected_bin_1 = -1
        if self.rti_config.config['Waves']['selected_bin_1'] != 'Disable':
            selected_bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])
        selected_bin_2 = -1
        if self.rti_config.config['Waves']['selected_bin_2'] != 'Disable':
            selected_bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])
        selected_bin_3 = -1
        if self.rti_config.config['Waves']['selected_bin_3'] != 'Disable':
            selected_bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])

        height_source = 4
        if self.rti_config.config['Waves']['height_source'] == 'Beam 0':
            height_source = 0
        if self.rti_config.config['Waves']['height_source'] == 'Beam 1':
            height_source = 1
        if self.rti_config.config['Waves']['height_source'] == 'Beam 2':
            height_source = 2
        if self.rti_config.config['Waves']['height_source'] == 'Beam 3':
            height_source = 3
        if self.rti_config.config['Waves']['height_source'] == 'Vertical':
            height_source = 4
        if self.rti_config.config['Waves']['height_source'] == 'Pressure':
            height_source = 5

        # Setup Waves Codec to generate waves MATLAB files
        self.waves_ens_count = 0
        self.wave_force_codec = WaveForceCodec(self.setup_vm.numBurstEnsSpinBox.value(),
                                               self.setup_vm.storagePathLineEdit.text(),
                                               lat=float(self.rti_config.config['Waves']['latitude']),
                                               lon=float(self.rti_config.config['Waves']['longitude']),
                                               bin1=selected_bin_1,
                                               bin2=selected_bin_2,
                                               bin3=selected_bin_3,
                                               ps_depth=float(self.rti_config.config['Waves']['pressure_sensor_height']),
                                               height_source=height_source,
                                               corr_thresh=float(self.rti_config.config['Waves']['corr_thresh']),
                                               pressure_offset=float(self.rti_config.config['Waves']['pressure_sensor_offset']))

        # Subscribe to receive ensembles and waves data
        self.adcp_codec.ensemble_event += self.ensemble_rcv
        self.wave_force_codec.process_data_event += self.waves_rcv

        # Subscribe to receive serial data
        self.terminal_vm.on_serial_data += self.serial_data_rcv
        self.setup_vm.on_waves_setting_change += self.update_waves_settings

        # Receive changes from setup
        self.setup_vm.folder_path_updated_sig.connect(self.folder_path_updated)

        # Reset the waves codec and AverageWaterColumn
        self.monitor_vm.reset_burst_progress_sig.connect(self.reset_waves_codec)
        self.monitor_vm.reset_avg_progress_sig.connect(self.reset_awc)

        # Monitor for average ensemble increment
        self.avg_water_vm.increment_ens_sig.connect(self.increment_avg_water_column)
        self.avg_water_vm.avg_taken_sig.connect(self.average_taken_awc)

    def shutdown(self):
        """
        Shutdown the object.
        :return:
        """
        self.adcp_codec.shutdown()

        # Shutdown the Ensemble thread
        self.ens_thread_alive = False
        self.ens_thread_event.set()

    def serial_data_rcv(self, sender, data):
        """
        Serial data received from the serial port.
        Pass the serial data to the ADCP Codec.
        :param sender:
        :param data: Serial data
        :return:
        """
        #self.logger.debug(str(sender))
        #self.logger.debug("Data Received: " + str(data))

        # Pass the data to codec to decode
        self.adcp_codec.add(data)

    def reset_waves_codec(self):
        """
        Reset the waves codec.  This will clear the buffer and restart
        the ensemble count.
        :return:
        """
        self.wave_force_codec.reset()

    def reset_awc(self):
        """
        Reset the Average Water Column average.
        This will clear the buffers.
        :return:
        """
        self.avg_water_vm.reset_average()

    def average_taken_awc(self):
        """
        Average taken in AverageWaterColumn.
        Reset the file tree.
        :return:
        """
        self.monitor_vm.refresh_file_tree_sig.emit()

        # Clear the counter
        self.avg_ens_count = 0

    def increment_avg_water_column(self, val):
        """
        Increment the average count.  The value is the
        current count.
        :param val: Current count in average.
        :return:
        """
        max_val = int(self.rti_config.config['AWC']['num_ensembles'])
        self.monitor_vm.increment_avg_value.emit(val, max_val)

    def ensemble_rcv(self, sender, ens):
        """
        Event when an ensemble is processed from the codec.
        :param sender:
        :param ens: Ensemble object
        :return:
        """
        """
        # Check if the data was a 4 beam or vertical beam data
        # Emit only on vertical beam data, because it is assumed
        # the data comes as a pair (4beam and vertical beam)
        # If the flag is set false, the count all the data
        if self.rti_config.config.getboolean('Waves', '4b_vert_pair'):
            if ens.IsEnsembleData and ens.EnsembleData.NumBeams == 1:
                # Emit signal that an ensemble was received
                self.monitor_vm.increment_burst_value.emit(max(self.wave_force_codec.TotalEnsInBurst, self.wave_force_codec.BufferCount),
                                                           self.setup_vm.numBurstEnsSpinBox.value())
        else:
            # Set the ensemble count for a burst
            self.monitor_vm.increment_burst_value.emit(max(self.wave_force_codec.TotalEnsInBurst, self.wave_force_codec.BufferCount),
                                                       self.setup_vm.numBurstEnsSpinBox.value())
        
                # If you find a vertical beam, set the right parameter in the config
                if ens.IsEnsembleData and ens.EnsembleData.NumBeams == 1:
                if not self.rti_config.config.getboolean("Waves", "4b_vert_pair"):
                    self.rti_config.config["Waves"]["4b_vert_pair"] = str("True")
                    self.rti_config.write()
        
        """

        # Add the data to the queue
        self.ens_queue.append(ens)

        # Wakeup the thread
        self.ens_thread_event.set()

    def ens_thread_run(self):
        """"
        Run a thread to handle the incoming ensemble data.
        Pass the data to the Waveforce codec and average water.
        """

        while self.ens_thread_alive:

            # Wait until the thread is awoken
            self.ens_thread_event.wait()

            # Check if data is in the queue
            while len(self.ens_queue) > 0:
                # Get the data from the queue
                ens = self.ens_queue.popleft()

                # Add the data to the WaveForce Codec
                self.wave_force_codec.add(ens)

                # Add the data to be averaged and displayed
                self.avg_water_vm.add_ens(ens)

                # Set the ensemble count for a burst
                # A check is done if the data includes vertical beam data or not
                if self.wave_force_codec.VertEnsCount == 0:
                    self.monitor_vm.increment_burst_value.emit(self.wave_force_codec.TotalEnsInBurst,
                                                               self.setup_vm.numBurstEnsSpinBox.value())
                else:
                    self.monitor_vm.increment_burst_value.emit(min(self.wave_force_codec.TotalEnsInBurst,
                                                                   self.wave_force_codec.VertEnsCount),
                                                               self.setup_vm.numBurstEnsSpinBox.value())
                # Increment Average Water Column monitor
                self.avg_ens_count += 1
                self.increment_avg_water_column(self.avg_ens_count)

                # if ens and ens.IsEnsembleData:
                #    self.logger.debug("ENS Received: " + str(ens.EnsembleData.EnsembleNumber))

            # Reset the event
            self.ens_thread_event.clear()

    def waves_rcv(self, sender, file_name):
        """
        A waves file was generated for AutoWaves.
        :param sender:
        :param file_name: File name of the file generated.
        :return:
        """
        # Reset the progress
        self.waves_ens_count = 0
        self.monitor_vm.reset_burst_progress_sig.emit()
        self.logger.debug("Waves File Complete: " + file_name)
        print(file_name)

        # Refresh the file tree
        self.monitor_vm.refresh_file_tree_sig.emit()

        # Display the Average Water Column data
        #self.avg_water_vm.display_data()

    def update_waves_settings(self, sender, num_ens, file_path, lat, lon, bin1, bin2, bin3, ps_depth, height_source, corr_thresh, pressure_offset):
        """
        Receive event that the settings changed and need to be updated.
        :param sender:
        :param num_ens: Number of ensembles in a burst.
        :param file_path: File path to store data
        :param lat:  Latitude
        :param lon:  Longitude
        :param bin1: Selected Bin 1.
        :param bin2: Selected Bin 2.
        :param bin3: Selected Bin 3.
        :param ps_depth: Pressure sensor depth.
        :param height_source: Height source.
        :param corr_thresh Correlation Threshold.
        :param pressure_offset Pressure sensor offset in meters.
        :return:
        """
        self.wave_force_codec.update_settings(ens_in_burst=num_ens,
                                              path=file_path,
                                              lat=lat,
                                              lon=lon,
                                              bin1=bin1,
                                              bin2=bin2,
                                              bin3=bin3,
                                              ps_depth=ps_depth,
                                              height_source=height_source,
                                              corr_thresh=corr_thresh,
                                              pressure_offset=pressure_offset)

    def folder_path_updated(self, folder_path):
        """
        Update the folder path from Setup VM to Monitor VM.
        Then update the config file so that all the output directory
        match.  In this application, they should store all the data
        to the same folder.
        :param folder_path: Updated folder path.
        :return:
        """
        # Update the file tree in Monitor
        self.monitor_vm.set_file_path_sig.emit(folder_path)

        # Set the output directory for all the sections so they are consistent
        self.rti_config.config['Waves']['output_dir'] = folder_path
        self.rti_config.config['Comm']['output_dir'] = folder_path
        self.rti_config.config['AWC']['output_dir'] = folder_path
        self.rti_config.write()

    def playback_file(self, files):
        """
        Playback the given files.  This will add all the data
        from the files into the codec.
        :param files: List of files.
        :return:
        """
        if files:
            # Reset all the monitors
            self.reset_waves_codec()
            self.reset_awc()

            self.logger.debug("Loading files: " + str(files))

        # Run a thread to playback the file
        thread = Thread(name="Playback Autowaves Mgr Thread", target=self.playback_thread, args=(files,))
        thread.start()

    def playback_thread(self, files):
        # Read the file
        for file in files:
            self.playback(file)

    def playback(self, file_path):
        """
        Playback the given file.  This will read the file
        then call ensemble_rcv to process the ensemble.
        :param file_path: Ensemble file path.
        :return:
        """
        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        BLOCK_SIZE = 4096

        # Create a buffer
        buff = bytes()

        with open(file_path, "rb") as f:

            # Set the statusbar with the file name
            self.parent.statusBar().showMessage("Loading file: " + file_path)
            self.logger.debug("Loading file: " + str(file_path))

            # Read in the file
            # for chunk in iter(lambda: f.read(4096), b''):
            #    self.adcp_codec.add(chunk)

            data = f.read(BLOCK_SIZE)  # Read in data

            while data:                                                 # Verify data was found
                buff += data                                            # Accumulate the buffer
                if DELIMITER in buff:                                   # Check for the delimiter
                    chunks = buff.split(DELIMITER)                      # If delimiter found, split to get the remaining buffer data
                    buff = chunks.pop()                                 # Put the remaining data back in the buffer

                    for chunk in chunks:                                # Take out the ens data
                        self.process_playback_ens(DELIMITER + chunk)    # Process the binary ensemble data

                data = f.read(BLOCK_SIZE)  # Read the next batch of data

                # Check if we need to shutdown
                if not self.ens_thread_alive:
                    return

        # Process whatever is remaining in the buffer
        self.process_playback_ens(DELIMITER + buff)

        # Close the file
        f.close()

    def process_playback_ens(self, ens_bin):
        # Verify the ENS data is good
        # This will check that all the data is there and the checksum is good
        if BinaryCodec.verify_ens_data(ens_bin):
            # Decode the ens binary data
            ens = BinaryCodec.decode_data_sets(ens_bin)

            # Pass the ensemble
            if ens:
                self.ensemble_rcv(None, ens)

                # Playback is too fast, so slow it down
                #time.sleep(0.01)
