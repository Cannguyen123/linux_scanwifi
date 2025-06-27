import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QInputDialog, QLineEdit
from PyQt6 import QtWidgets
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer
from backend import get_wifi_info, connect_to_wifi, load_passwords, save_password
from update2 import Ui_MainWindow
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime

from update2 import Ui_MainWindow
from backend import scan_wifi_to_list, initialize_wifi_interface, find_strongest_ap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tableWidget.setColumnCount(4)
        self.ui.tableWidget.setHorizontalHeaderLabels(["SSID", "Tín hiệu", "Bảo mật", "MAC"])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.strongest_label = QtWidgets.QLabel(self.ui.widget)
        self.strongest_label.setGeometry(20, 20, 700, 40)
        self.strongest_label.setStyleSheet("color: black; font-weight: bold;")
        self.strongest_label.setText("Đang quét Wi-Fi...")

        self.scan_button = QtWidgets.QPushButton("Quét lại", self.ui.widget)
        self.scan_button.setGeometry(20, 70, 100, 30)
        self.scan_button.clicked.connect(self.update_network_info)

        self.passwords = load_passwords()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_network_info)
        self.timer.start(5000)

        self.update_network_info()
        ### đồ thi cho strongest
        self.timestamps = []
        self.signal_strengths = []

        self.setup_graph()

        # Timer để cập nhật đồ thị mỗi giây
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(10000)  # mỗi 1000 ms = 1 giây

    def update_network_info(self):
        info = get_wifi_info()
        wifi_list = info['list']
        strongest_ap = info['strongest']
        connected_ssid = info['connected']
        iface = info['iface']

        self.ui.statusbar.showMessage(f"Tìm thấy {len(wifi_list)} mạng Wi-Fi.")
        self.ui.tableWidget.setRowCount(len(wifi_list))

        for row, ap in enumerate(wifi_list):
            ssid = ap['SSID']
            signal = str(ap['Signal'])
            auth = ", ".join([str(a) for a in ap['Auth']]) or "OPEN"
            mac = ap['MAC']
            for col, val in enumerate([ssid, signal, auth, mac]):
                item = QTableWidgetItem(val)
                item.setForeground(QColor("#e0e0e0"))
                item.setBackground(QColor("#444444"))
                item.setFont(QFont("Roboto", 11, QFont.Weight.Bold))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.ui.tableWidget.setItem(row, col, item)

        if strongest_ap:
            ssid = strongest_ap['SSID'] or "<Mạng ẩn>"
            signal = strongest_ap['Signal']
            mac = strongest_ap['MAC']
            self.strongest_label.setText(f"Mạng mạnh nhất: SSID: {ssid}, Tín hiệu: {signal}, MAC: {mac}")

            if connected_ssid != ssid:
                password = self.passwords.get(ssid, "")
                if not password:
                    password, ok = QInputDialog.getText(self, "Nhập mật khẩu", f"Nhập mật khẩu cho {ssid}:", QLineEdit.EchoMode.Password)
                    if ok and password:
                        self.passwords[ssid] = password
                        save_password(self.passwords)
                    else:
                        self.strongest_label.setText("Hủy kết nối do không có mật khẩu.")
                        return
                if connect_to_wifi(iface, ssid, password):
                    self.strongest_label.setText(f"Đã kết nối thành công với {ssid}")
                else:
                    self.strongest_label.setText(f"Không thể kết nối vào {ssid}. Kiểm tra mật khẩu hoặc tín hiệu.")
        else:
            self.strongest_label.setText("Không tìm thấy mạng mạnh nhất để kết nối.")





    #tab_4 graph strongest
    def setup_graph(self):
        # Tạo Figure và Canvas
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.figure.patch.set_facecolor('#333333')
        self.ax.set_facecolor('#222222')

        # Gắn vào layout của tab_4
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.ui.tab_4.setLayout(layout)

    def update_graph(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.timestamps.append(current_time)

        iface = initialize_wifi_interface()
        wifi_list = scan_wifi_to_list(iface)
        strong_ap = find_strongest_ap(wifi_list)
        signal = strong_ap["Signal"]
        self.signal_strengths.append(signal)

        print(f"{current_time}: RSSI = {signal} dBm")

        # Giới hạn số điểm hiển thị
        if len(self.timestamps) > 20:
            self.timestamps.pop(0)
            self.signal_strengths.pop(0)

        # Cập nhật đồ thị
        self.ax.clear()
        self.ax.plot(self.timestamps, self.signal_strengths, marker='o', linestyle='-', color='cyan')
        self.ax.set_xlabel("Thời gian", color='white')
        self.ax.set_ylabel("Cường độ tín hiệu (dBm)", color='white')
        self.ax.set_title("Tín hiệu Wi-Fi theo thời gian (Real-time)", color='white')
        self.ax.tick_params(axis='x', rotation=45, colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.grid(True, color='gray', linestyle='--', alpha=0.5)
        self.figure.tight_layout()

        self.canvas.draw()  # cập nhật canvas

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
