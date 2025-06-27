import os.path
import json
import time
import subprocess
from pywifi import PyWiFi, const, Profile

# Tên file dùng để lưu mật khẩu Wi-Fi ở dạng JSON
PASS_WORD_FILE = "save_pW.py"


# Hàm đọc mật khẩu từ file JSON nếu có
def load_passwords():
    if os.path.exists(PASS_WORD_FILE):
        try:
            with open(PASS_WORD_FILE, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except json.JSONDecodeError:
            print("File JSON bị lỗi, đang khởi tạo lại...")
            return {}
    return {}


# Hàm lưu mật khẩu Wi-Fi vào file JSON
def save_password(passwords):
    with open(PASS_WORD_FILE, 'w') as f:
        json.dump(passwords, f, indent=4)


# Hàm khởi tạo interface Wi-Fi (dùng interface đầu tiên trên máy)
def initialize_wifi_interface():
    wifi = PyWiFi()
    return wifi.interfaces()[0]  # Sử dụng interface đầu tiên


# Hàm quét các mạng Wi-Fi xung quanh và trả về danh sách đã sắp xếp theo cường độ tín hiệu
def scan_wifi_to_list(iface):
    iface.scan()  # Gửi lệnh quét
    time.sleep(5)  # Đợi kết quả quét
    scan_results = iface.scan_results()

    wifi_list = []
    for ap in scan_results:
        wifi_list.append({
            "SSID": ap.ssid,
            "Signal": ap.signal,
            "Auth": ap.akm,
            "MAC": ap.bssid
        })

    # Sắp xếp danh sách theo tín hiệu giảm dần
    wifi_list.sort(key=lambda x: x['Signal'], reverse=True)
    return wifi_list


# Hàm tìm Access Point (AP) có tín hiệu mạnh nhất
def find_strongest_ap(wifi_list):
    return max(wifi_list, key=lambda wifi: wifi["Signal"], default=None)


# Hàm lấy SSID hiện tại mà máy đang kết nối (Windows)
def get_current_ssid():
    try:
        output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('utf-8', errors='ignore')
        for line in output.split('\n'):
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":")[1].strip()
                return ssid if ssid else None
        return None
    except Exception as e:
        print("Lỗi lấy SSID hiện tại:", e)
        return None


# Hàm kết nối tới Wi-Fi với SSID và mật khẩu được cung cấp
def connect_to_wifi(iface, ssid, password=""):
    # Nếu đã kết nối đúng SSID rồi thì không cần kết nối lại
    if iface.status() == const.IFACE_CONNECTED and get_current_ssid() == ssid:
        return True

    # Ngắt kết nối hiện tại
    iface.disconnect()
    time.sleep(1)

    # Tạo profile mới cho Wi-Fi
    profile = Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.cipher = const.CIPHER_TYPE_CCMP
    profile.key = password

    # Xóa các profile cũ và thêm profile mới
    iface.remove_all_network_profiles()
    tmp_profile = iface.add_network_profile(profile)

    # Tiến hành kết nối
    iface.connect(tmp_profile)
    time.sleep(5)

    return iface.status() == const.IFACE_CONNECTED


# Hàm tổng hợp thông tin về Wi-Fi hiện tại: danh sách mạng, mạng mạnh nhất và mạng đang kết nối
def get_wifi_info():
    iface = initialize_wifi_interface()
    wifi_list = scan_wifi_to_list(iface)
    return {
        "iface": iface,
        "list": wifi_list,
        "strongest": find_strongest_ap(wifi_list),
        "connected": get_current_ssid()
    }
