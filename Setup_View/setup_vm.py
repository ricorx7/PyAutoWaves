from PyQt5.QtWidgets import QWidget
from . import setup_view
import rti_python.Comm.adcp_serial_port as adcp_serial
import threading
import time
import serial


class SetupVM(setup_view.Ui_Setup, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    def __init__(self, parent):
        setup_view.Ui_Setup.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.adcp = None
        self.adcp_thread = None
        self.adcp_thread_alive = False

        self.MAX_SERIAL_CONSOLE_LEN = 5000

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
        self.serialTextBrowser.ensureCursorVisible()
        self.serialTextBrowser.textChanged.connect(self.serial_text_changed)

        # Setup buttons
        self.scanSerialPushButton.clicked.connect(self.update_serial_list)
        self.serialConnectPushButton.clicked.connect(self.connect_serial)
        self.serialDisconnectPushButton.clicked.connect(self.disconnect_serial)
        self.breakPushButton.clicked.connect(self.serial_break)
        self.sendCmdPushButton.clicked.connect(self.send_cmd)
        self.startPingPushButton.clicked.connect(self.start_pinging)
        self.stopPingPushButton.clicked.connect(self.stop_pinging)

    def update_serial_list(self):
        """
        Ste the serial ports to the list.
        :return:
        """
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
        print("Serial Connect: " + port + " : " + self.baudComboBox.currentText())
        self.serialTextBrowser.append("Serial Connect: " + port + " : " + self.baudComboBox.currentText())

        try:
            self.adcp = adcp_serial.AdcpSerialPort(port, baud)
            self.adcp.connect()
        except ValueError as ve:
            self.serialTextBrowser.append("Error opening serial port. " + str(ve))
            return
        except serial.SerialException as se:
            self.serialTextBrowser.append("Error opening serial port. " + str(se))
            return
        except Exception as e:
            self.serialTextBrowser.append("Error opening serial port. " + str(e))
            return

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

    def serial_break(self):
        # Clear the display
        self.serialTextBrowser.setPlainText("")

        if self.adcp:
            self.adcp.send_break(1.5)

    def send_cmd(self):
        if self.adcp:
            if len(self.cmdLineEdit.text()) > 0:
                self.adcp.send_cmd(self.cmdLineEdit.text())
                print("Write to serial port: " + self.cmdLineEdit.text())

                # Clear the text
                self.cmdLineEdit.setText("")

    def start_pinging(self):
        if self.adcp:
            self.adcp.start_pinging()

    def stop_pinging(self):
        if self.adcp:
            self.adcp.stop_pinging()

    def shutdown(self):
        self.disconnect_serial()

    def serial_text_changed(self):
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
            serial_text = serial_text.replace(str(chr(6)), '<span style="background-color: #339cff"> ACK</span>')
            self.set_serial_text(serial_text)

        # Change the NCK to colored NCK
        if str(chr(21)) in serial_text:
            serial_text = serial_text.replace(str(chr(21)), '<span style="background-color: red"> NCK</span>')
            self.set_serial_text(serial_text)


    def set_serial_text(self, txt):
        self.serialTextBrowser.blockSignals(True)  # Prevent this from being called again
        self.serialTextBrowser.setHtml(txt)
        self.serialTextBrowser.blockSignals(False)



def thread_worker(vm):
    while vm.adcp_thread_alive:
        if vm.adcp.raw_serial.in_waiting:
            data = vm.adcp.read(vm.adcp.raw_serial.in_waiting).decode('ascii')
            vm.serialTextBrowser.append(data)
        time.sleep(0.01)
