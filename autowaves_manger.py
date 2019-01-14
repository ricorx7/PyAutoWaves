import logging
from rti_python.Codecs.AdcpCodec import AdcpCodec


class AutoWavesManager:
    def __init__(self, terminal_vm, setup_vm, monitor_vm):
        self.terminal_vm = terminal_vm
        self.setup_vm = setup_vm
        self.monitor_vm = monitor_vm

        self.adcp_codec = AdcpCodec()
        self.adcp_codec.enable_waveforce_codec(self.setup_vm.numBurstEnsSpinBox.value(),
                                               self.setup_vm.storagePathLineEdit.text(),
                                               lat=0.0,
                                               lon=0.0,
                                               bin1=3,
                                               bin2=4,
                                               bin3=5,
                                               ps_depth=30)
        self.adcp_codec.EnsembleEvent += self.ensemble_rcv
        self.adcp_codec.publish_waves_event += self.waves_rcv

        # Subscribe to receiver serial data
        self.terminal_vm.on_serial_data += self.serial_data_rcv
        self.setup_vm.on_waves_setting_change += self.update_waves_settings

        # Receive changes from setup
        self.setup_vm.folder_path_updated_sig.connect(self.folder_path_updated)

    def serial_data_rcv(self, sender, data):
        logging.debug(str(sender))
        logging.debug("Data Received: " + str(data))

        # Pass the data to codec to decode
        self.adcp_codec.add(data)

    def ensemble_rcv(self, sender, ens):
        self.monitor_vm.increment_value.emit(self.setup_vm.numBurstEnsSpinBox.value())      # Emit signal
        logging.debug("ENS Received: " + str(ens.EnsembleData.EnsembleNumber))

    def waves_rcv(self, sender, file_name):
        self.monitor_vm.reset_progress_sig.emit()
        logging.debug("Waves File Complete: " + file_name)

    def update_waves_settings(self, sender, num_ens, file_path):
        """
        Receive event that the settings changed and need to be updated.
        :param sender:
        :param num_ens: Number of ensembles in a burst.
        :param file_path: File path to store data
        :return:
        """
        self.adcp_codec.update_settings_waveforce_codec(ens_in_burst=num_ens,
                                                        path=file_path,
                                                        lat=0.0,
                                                        lon=0.0,
                                                        bin1=3,
                                                        bin2=4,
                                                        bin3=5,
                                                        ps_depth=30)

    def folder_path_updated(self, folder_path):
        self.monitor_vm.set_file_path_sig.emit(folder_path)
