import time
from datetime import datetime
import matplotlib.pyplot as plt

from backend import scan_wifi_to_list, initialize_wifi_interface, find_strongest_ap

timestamps = []
signal_strengths = []

plt.ion()
fig, ax = plt.subplots()
fig.patch.set_facecolor('#333333')
ax.set_facecolor('#222222')

while True:
    current_time = datetime.now().strftime("%H:%M:%S")
    timestamps.append(current_time)

    iface = initialize_wifi_interface()
    wifi_list = scan_wifi_to_list(iface)
    strong_ap = find_strongest_ap(wifi_list)
    signal = strong_ap["Signal"]
    signal_strengths.append(signal)

    print(f"{current_time}: RSSI = {signal} dBm")

    ax.clear()  # Xoá nội dung cũ trên axes

    # Vẽ đồ thị mới lên ax
    ax.plot(timestamps, signal_strengths, marker='o', linestyle='-', color='cyan')
    ax.set_xlabel("Thời gian", color='white')
    ax.set_ylabel("Cường độ tín hiệu (dBm)", color='white')
    ax.set_title("Tín hiệu Wi-Fi theo thời gian (Real-time)", color='white')
    ax.tick_params(axis='x', rotation=45, colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.grid(True, color='gray', linestyle='--', alpha=0.5)
    fig.tight_layout()

    plt.pause(5)

    if len(timestamps) > 100:
        timestamps.pop(0)
        signal_strengths.pop(0)
