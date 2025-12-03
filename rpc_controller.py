import sys
import time
import traceback
from pypresence import Presence
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QLineEdit, QTextEdit, QVBoxLayout, QGridLayout
)

CLIENT_ID = "your client id"



class RPCThread(QThread):
    log = pyqtSignal(str)

    def __init__(self, payload_func):
        super().__init__()
        self.payload_func = payload_func
        self.running = True
        self.rpc = None

    def run(self):
        while self.running:
            try:
                # Connect if not already connected
                if self.rpc is None:
                    self.log.emit("Connecting to Discord RPC")
                    self.rpc = Presence(CLIENT_ID)
                    self.rpc.connect()
                    self.log.emit("Connected")

                # Get payload from GUI side
                payload = self.payload_func()
                if payload:
                    self.rpc.update(**payload)
                    self.log.emit("Status updated.")
                else:
                    self.log.emit("No payload to update.")

                time.sleep(10)

            except Exception as e:
                self.log.emit(f"RPC Error: {e}")
                traceback.print_exc()
                self.rpc = None
                time.sleep(3)  # retry delay

    def stop(self):
        self.running = False
        try:
            if self.rpc:
                self.rpc.clear()
                self.rpc.close()
        except:
            pass


# ui
class RPCGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord RPC Controller")
        self.setGeometry(200, 200, 450, 350)
        self.setStyleSheet("font-size: 14px;")

        layout = QVBoxLayout()

        grid = QGridLayout()

        self.details = QLineEdit()
        self.state = QLineEdit()
        
        self.large_image = QLineEdit()
        self.large_text = QLineEdit()

        grid.addWidget(QLabel("Details:"), 0, 0)
        grid.addWidget(self.details, 0, 1)
        grid.addWidget(QLabel("State:"), 1, 0)
        grid.addWidget(self.state, 1, 1)

        grid.addWidget(QLabel("Large Image Key:"), 2, 0)
        grid.addWidget(self.large_image, 2, 1)
        grid.addWidget(QLabel("Large Image Text:"), 3, 0)
        grid.addWidget(self.large_text, 3, 1)

        layout.addLayout(grid)

        self.start_btn = QPushButton("Start RPC")
        self.stop_btn = QPushButton("Stop RPC")
        self.stop_btn.setEnabled(False)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        self.log_field = QTextEdit()
        self.log_field.setReadOnly(True)
        layout.addWidget(self.log_field)

        self.setLayout(layout)

        # Connect buttons
        self.start_btn.clicked.connect(self.start_rpc)
        self.stop_btn.clicked.connect(self.stop_rpc)

        self.rpc_thread = None

    def log(self, msg):
        self.log_field.append(msg)

    def build_payload(self):
        return {
            "details": self.details.text(),
            "state": self.state.text(),
            "large_image": self.large_image.text() or None,
            "large_text": self.large_text.text() or None
        }

    def start_rpc(self):
        if self.rpc_thread:
            return

        self.log("Starting RPC")

        self.rpc_thread = RPCThread(self.build_payload)
        self.rpc_thread.log.connect(self.log)
        self.rpc_thread.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_rpc(self):
        if self.rpc_thread:
            self.log("Stopping RPC")
            self.rpc_thread.stop()
            self.rpc_thread.quit()
            self.rpc_thread.wait()
            self.rpc_thread = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log("RPC stopped.")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RPCGui()
    window.show()
    sys.exit(app.exec_())
