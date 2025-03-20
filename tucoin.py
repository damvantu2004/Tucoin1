#!/usr/bin/env python3
import os
import sys
import threading
import time
import argparse
from src.blockchain import Blockchain
from src.wallet import Wallet
from src.network import Network
from src.consensus import set_consensus
from ui.main_window import MainWindow

def create_data_dir():
    """Tạo thư mục data nếu chưa tồn tại"""
    os.makedirs("data", exist_ok=True)

def main():
    """Hàm chính của ứng dụng"""
    # Xử lý tham số dòng lệnh
    parser = argparse.ArgumentParser(description='TuCoin Blockchain App')
    parser.add_argument('--port', type=int, default=5000, help='Cổng để lắng nghe (mặc định: 5000)')
    parser.add_argument('--connect', type=str, help='Địa chỉ IP:Port để kết nối khi khởi động')
    args = parser.parse_args()
    
    port = args.port
    connect_to = args.connect
    
    print(f"Khởi động TuCoin Blockchain App trên cổng {port}...")
    
    # Tạo thư mục data
    create_data_dir()
    
    # Khởi tạo blockchain
    blockchain = Blockchain()
    
    # Tải blockchain từ file nếu có
    if os.path.exists("data/blockchain.json"):
        print("Đang tải blockchain từ file...")
        blockchain.load_from_file()
    
    # Khởi tạo ví
    wallet = Wallet(blockchain)
    
    # Tải ví từ file nếu có
    if os.path.exists("data/wallet.json"):
        print("Đang tải ví từ file...")
        wallet.load_from_file()
    else:
        # Tạo ví mới nếu chưa có
        print("Tạo ví mới...")
        wallet.create_address()
        wallet.save_to_file()
    
    # Khởi tạo network với cổng được chỉ định
    network = Network(blockchain, port)
    
    # Khởi động server
    print("Khởi động server mạng...")
    if network.start_server():
        print(f"Server đang lắng nghe tại {network.get_local_ip()}:{network.port}")
    else:
        print("Không thể khởi động server mạng. Ứng dụng sẽ chạy ở chế độ offline.")
    
    # Kết nối đến node khác nếu được chỉ định
    if connect_to:
        try:
            ip, connect_port = connect_to.split(':')
            connect_port = int(connect_port)
            print(f"Đang kết nối đến node {ip}:{connect_port}...")
            
            # Tạo thread để kết nối (tránh block giao diện)
            def connect_thread():
                time.sleep(2)  # Đợi server khởi động
                if network.connect_to_node(ip, connect_port):
                    print(f"Đã kết nối thành công đến {ip}:{connect_port}")
                else:
                    print(f"Không thể kết nối đến {ip}:{connect_port}")
            
            threading.Thread(target=connect_thread, daemon=True).start()
        except Exception as e:
            print(f"Lỗi khi phân tích địa chỉ kết nối: {e}")
    
    # Tạo thread để tự động lưu blockchain và ví
    def auto_save():
        while True:
            time.sleep(60)  # Lưu mỗi 60 giây
            try:
                blockchain.save_to_file()
                wallet.save_to_file()
                print("Đã tự động lưu blockchain và ví")
            except Exception as e:
                print(f"Lỗi khi tự động lưu: {e}")
    
    save_thread = threading.Thread(target=auto_save, daemon=True)
    save_thread.start()
    
    # Khởi động giao diện người dùng
    print("Khởi động giao diện người dùng...")
    app = MainWindow(blockchain, wallet, network)
    
    # Đặt tiêu đề cửa sổ để phân biệt các node
    app.root.title(f"TuCoin Blockchain App - Node {port}")
    
    app.run()
    
    # Lưu dữ liệu trước khi thoát
    print("Đang lưu dữ liệu trước khi thoát...")
    blockchain.save_to_file()
    wallet.save_to_file()
    
    print("Ứng dụng đã đóng.")

if __name__ == "__main__":
    main()
