from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QThread, pyqtSlot, QObject, pyqtSignal
from . import terminal_view
import rti_python.Comm.adcp_serial_port as adcp_serial
import rti_python.Writer.rti_binary as RtiBinaryWriter
import threading
import time
import serial
import logging
from obsub import event


class TerminalVM(terminal_view.Ui_Terminal, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    # Create a signal to update the GUI on another thread
    display_console_data_changed = pyqtSignal(str)

    def __init__(self, parent):
        terminal_view.Ui_Terminal.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.adcp = None
        self.adcp_thread = None
        self.adcp_thread_alive = False

        # Connect signal and slot for multithread updating GUI
        self.display_console_data_changed.connect(self.display_console)

        self.serial_recorder = None

        self.MAX_SERIAL_CONSOLE_LEN = 9000

        self.init_display()

    def init_display(self):
        """
        Initialize the display.
        :return:
        """
        # Set the serial port list and baud list
        self.update_serial_list()
        self.serialPortComboBox.setToolTip("If no serial ports are list, make sure it is available and click the scan button to update the serial port list.")
        self.scanSerialPushButton.setToolTip("Scan for any available serial ports.  If nothing is listed, then there are no available serial ports.  Close any applications using a serial port.")
        self.update_baud_rate_list()
        self.baudComboBox.setCurrentText("115200")
        self.baudComboBox.setToolTip("The default baud rate is 115200.")
        #self.serialTextBrowser.ensureCursorVisible()
        self.serialTextBrowser.textChanged.connect(self.serial_text_changed)

        # Setup buttons
        self.scanSerialPushButton.clicked.connect(self.update_serial_list)
        self.serialConnectPushButton.clicked.connect(self.connect_serial)
        self.serialDisconnectPushButton.clicked.connect(self.disconnect_serial)
        self.breakPushButton.clicked.connect(self.serial_break)
        self.sendCmdPushButton.clicked.connect(self.send_cmd)
        self.startPingPushButton.clicked.connect(self.start_pinging)
        self.stopPingPushButton.clicked.connect(self.stop_pinging)
        self.recordPushButton.clicked.connect(self.turn_on_off_record)
        self.clearConsolePushButton.clicked.connect(self.clear_console)
        self.clearBulkCmdPushButton.clicked.connect(self.clear_bulk_cmd)
        self.sendBulkCmdPushButton.clicked.connect(self.send_bulk_cmd)

    def update_serial_list(self):
        """
        Ste the serial ports to the list.
        :return:
        """
        # Clear the current list
        self.serialPortComboBox.clear()

        # Add all the found serial ports
        for port in adcp_serial.get_serial_ports():
            self.serialPortComboBox.addItem(port)

    def update_baud_rate_list(self):
        """
        Set the baud rates to the list.
        :return:
        """
        self.baudComboBox.addItems(adcp_serial.get_baud_rates())

    def connect_serial(self):
        """
        Connect the serial port and the read thread.
        :return:
        """
        port = self.serialPortComboBox.currentText()
        baud = int(self.baudComboBox.currentText())
        logging.debug("Serial Connect: " + port + " : " + self.baudComboBox.currentText())
        self.serialTextBrowser.append("Serial Connect: " + port + " : " + self.baudComboBox.currentText())

        try:
            self.adcp = adcp_serial.AdcpSerialPort(port, baud)
        except ValueError as ve:
            self.serialTextBrowser.append("Error opening serial port. " + str(ve))
            logging.error("Error opening serial port. " + str(ve))
            return
        except serial.SerialException as se:
            self.serialTextBrowser.append("Error opening serial port. " + str(se))
            logging.error("Error opening serial port. " + str(se))
            return
        except Exception as e:
            self.serialTextBrowser.append("Error opening serial port. " + str(e))
            logging.error("Error opening serial port. " + str(e))
            return

        # Start the read thread
        self.adcp_thread_alive = True
        self.adcp_thread = threading.Thread(target=thread_worker, args=(self,))
        self.adcp_thread.start()

        # Disable buttons
        self.serialConnectPushButton.setDisabled(True)
        self.baudComboBox.setDisabled(True)
        self.serialPortComboBox.setDisabled(True)
        self.scanSerialPushButton.setDisabled(True)

    def disconnect_serial(self):
        """
        Disconnect the serial port and stop the read thread.
        :return:
        """
        print("Serial Disconnect")
        self.adcp_thread_alive = False

        if self.adcp:
            self.adcp.disconnect()
            self.adcp = None

        self.serialConnectPushButton.setDisabled(False)
        self.baudComboBox.setDisabled(False)
        self.serialPortComboBox.setDisabled(False)
        self.scanSerialPushButton.setDisabled(False)
        self.serialTextBrowser.append("Serial Disconnect.")
        logging.debug("Serial Disconnect")

    def serial_break(self):
        """
        Send a BREAK to the serial port.
        :return:
        """
        # Clear the display
        self.serialTextBrowser.setPlainText("")

        # Send a BREAK
        if self.adcp:
            self.adcp.send_break(1.25)
            logging.debug("BREAK SENT")

    def send_cmd(self):
        """
        Send a command to the ADCP.
        :return:
        """
        if self.adcp:
            if len(self.cmdLineEdit.text()) > 0:
                self.adcp.send_cmd(self.cmdLineEdit.text())
                logging.debug("Write to serial port: " + self.cmdLineEdit.text())

                # Clear the text
                self.cmdLineEdit.setText("")

    def start_pinging(self):
        """
        Send the command to start pinging.
        :return:
        """
        if self.adcp:
            self.adcp.start_pinging()
            logging.debug("Start Pinging")

    def stop_pinging(self):
        """
        Send the command to stop pinging.
        :return:
        """
        if self.adcp:
            self.serialTextBrowser.setHtml("")
            self.adcp.stop_pinging()
            logging.debug("Stop Pinging")

    def shutdown(self):
        """
        Shutdown the VM.
        :return:
        """
        logging.debug("Shutdown Terminal VM")
        self.disconnect_serial()

        if self.serial_recorder:
            self.serial_recorder.close()

    def serial_text_changed(self):
        """
        Eventhandler when the serial console is updated.
        :return:
        """
        serial_text = self.serialTextBrowser.toHtml()

        # Remove the excess characters
        serial_text_len = len(serial_text)
        if serial_text_len > self.MAX_SERIAL_CONSOLE_LEN:
            # Reduce the string size
            serial_text = serial_text[serial_text_len - self.MAX_SERIAL_CONSOLE_LEN:]

            # Set the text to the display
            self.set_serial_text(serial_text)

        # Change the ACK to colored ACK
        if str(chr(6)) in serial_text:
            serial_text = serial_text.replace(str(chr(6)), '<span style="background-color: #339cff">ACK</span>')
            self.set_serial_text(serial_text)

        # Change the NCK to colored NCK
        if str(chr(21)) in serial_text:
            serial_text = serial_text.replace(str(chr(21)), '<span style="background-color: red">NCK</span>')
            serial_text = serial_text + '<span style="background-color: red">Bad Command</span>'
            self.set_serial_text(serial_text)

    def set_serial_text(self, txt):
        """
        Set the text to the serial console display.  This will block the signal
        from calling the event handler of the update.  That way the display will
        not recursively call itself and also not process the text.
        :param txt: Text to display
        :return:
        """
        self.serialTextBrowser.blockSignals(True)  # Prevent this from being called again
        self.serialTextBrowser.setHtml(txt)
        self.serialTextBrowser.blockSignals(False)

    def turn_on_off_record(self):
        if self.recordPushButton.isChecked():
            self.serial_recorder = RtiBinaryWriter.RtiBinaryWriter()
            logging.debug("Start Recording")
        else:
            if self.serial_recorder:
                self.serial_recorder.close()
                logging.debug("Stop Recording")
            self.serial_recorder = None

    def record_data(self, data):
        if self.serial_recorder:
            self.serial_recorder.write(data)
            self.bytesWrittenLabel.setText(self.serial_recorder.get_bytes_written())

    def clear_console(self):
        self.serialTextBrowser.setHtml("")

    def clear_bulk_cmd(self):
        self.bulkCmdMlainTextEdit.setPlainText("")

    def send_bulk_cmd(self):
        cmds = self.bulkCmdMlainTextEdit.toPlainText().splitlines()
        for cmd in cmds:
            self.adcp.send_cmd(cmd + "\n")
            logging.debug("Write to serial port: " + cmd)
            time.sleep(0.25)

    @event
    def on_serial_data(self, data):
        """
        Subscribe to receive serial data.
        :param data: Data from the serial port.
        :return:
        """
        logging.debug("Data Received")

    @pyqtSlot(str)
    def display_console(self, data):
        """
        Create a slot to update the GUI on another thread.
        :param data:
        :return:
        """
        self.serialTextBrowser.setText(self.serialTextBrowser.toPlainText() + data)


def thread_worker(vm):
    """
    Thread worker to handle reading the serial port.
    :param vm: This VM to get access to the variables.
    :return:
    """
    while vm.adcp_thread_alive:
        if vm.adcp.raw_serial.in_waiting:
            # Read the data from the serial port
            data = vm.adcp.read(vm.adcp.raw_serial.in_waiting)

            try:
                ascii_data = data.decode('ascii')
                vm.display_console_data_changed.emit(ascii_data)        # Emit signal
                logging.debug(ascii_data)
            except Exception:
                # Do nothing
                vm.display_console_data_changed.emit(str(data))         # Emit signal

            # Record data if turned on
            vm.record_data(data)

            # Publish the data
            vm.on_serial_data(data)

        time.sleep(0.01)
