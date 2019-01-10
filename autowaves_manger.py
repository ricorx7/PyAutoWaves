import logging
from rti_python.Codecs.AdcpCodec import AdcpCodec


class AutoWavesManager():
    def __init__(self, terminal_vm, setup_vm, monitor_vm):
        self.terminal_vm = terminal_vm
        self.setup_vm = setup_vm
        self.monitor_vm = monitor_vm

        self.adcp_codec = AdcpCodec()
        self.adcp_codec.EnsembleEvent += self.ensemble_rcv

        # Subscribe to receiver serial data
        self.terminal_vm.on_serial_data += self.serial_data_rcv

    def serial_data_rcv(self, sender, data):
        logging.debug(str(sender))
        logging.debug("Data Received: " + str(data))

        # Pass the data to codec to decode
        self.adcp_codec.add(data)

    def ensemble_rcv(self, sender, ens):
        #self.monitor_vm.progressBar.setValue(self.monitor_vm.progressBar.value() + 1)
        logging.debug("ENS Received: " + str(ens.EnsembleData.EnsembleNumber))
