import logging
from rti_python.Codecs.AdcpCodec import AdcpCodec


class AutoWavesManager():
    def __init__(self, terminal_vm, setup_vm, monitor_vm):
        self.terminal_vm = terminal_vm
        self.setup_vm = setup_vm
        self.monitor_vm = monitor_vm

        self.adcp_codec = AdcpCodec()
        self.adcp_codec.enable_waveforce_codec(10,
                                            #self.setup_vm.numBurstEnsSpinBox.value(),
                                               self.setup_vm.storagePathLineEdit.text(),
                                               lat=0.0,
                                               lon=0.0,
                                               bin1=3,
                                               bin2=4,
                                               bin3=5,
                                               ps_depth=30)
        self.adcp_codec.EnsembleEvent += self.ensemble_rcv
        self.adcp_codec.process_wave_data += self.waves_rcv

        # Subscribe to receiver serial data
        self.terminal_vm.on_serial_data += self.serial_data_rcv

    def serial_data_rcv(self, sender, data):
        logging.debug(str(sender))
        logging.debug("Data Received: " + str(data))

        # Pass the data to codec to decode
        self.adcp_codec.add(data)

    def ensemble_rcv(self, sender, ens):
        #self.monitor_vm.increment_progress(self.setup_vm.numBurstEnsSpinBox.value())
        self.monitor_vm.increment_value.emit(self.setup_vm.numBurstEnsSpinBox.value())      # Emit signal
        logging.debug("ENS Received: " + str(ens.EnsembleData.EnsembleNumber))

    def waves_rcv(self, sender, file_name):
        self.monitor_vm.reset_progress.emit()
        logging.debug("Waves File Complete: " + file_name)
