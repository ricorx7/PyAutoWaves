import logging
from rti_python.Codecs.AdcpCodec import AdcpCodec
from rti_python.Utilities.config import RtiConfig


class AutoWavesManager:
    def __init__(self, terminal_vm, setup_vm, monitor_vm, avg_water_vm):
        self.terminal_vm = terminal_vm
        self.setup_vm = setup_vm
        self.monitor_vm = monitor_vm
        self.avg_water_vm = avg_water_vm

        self.rti_config = RtiConfig()

        self.adcp_codec = AdcpCodec()

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
        self.adcp_codec.enable_waveforce_codec(self.setup_vm.numBurstEnsSpinBox.value(),
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
        self.adcp_codec.EnsembleEvent += self.ensemble_rcv
        self.adcp_codec.publish_waves_event += self.waves_rcv

        # Subscribe to receive serial data
        self.terminal_vm.on_serial_data += self.serial_data_rcv
        self.setup_vm.on_waves_setting_change += self.update_waves_settings

        # Receive changes from setup
        self.setup_vm.folder_path_updated_sig.connect(self.folder_path_updated)

    def shutdown(self):
        self.adcp_codec.shutdown()

    def serial_data_rcv(self, sender, data):
        logging.debug(str(sender))
        logging.debug("Data Received: " + str(data))

        # Pass the data to codec to decode
        self.adcp_codec.add(data)

    def ensemble_rcv(self, sender, ens):
        """
        Event when an ensemble is processed from the codec.
        :param sender:
        :param ens: Ensemble object
        :return:
        """
        self.monitor_vm.increment_value.emit(self.setup_vm.numBurstEnsSpinBox.value())      # Emit signal
        #self.avg_water_vm.add_ens_sig.emit(ens)
        self.avg_water_vm.add_ens(ens)
        logging.debug("ENS Received: " + str(ens.EnsembleData.EnsembleNumber))

    def waves_rcv(self, sender, file_name):
        self.monitor_vm.reset_progress_sig.emit()
        logging.debug("Waves File Complete: " + file_name)

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

        self.adcp_codec.update_settings_waveforce_codec(ens_in_burst=num_ens,
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
            print(files)

        # Read the file
        for file in files:
            with open(file, "rb") as f:
                for line in f:
                    # Pass it to the codec
                    self.adcp_codec.add(line)

