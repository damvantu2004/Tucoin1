import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# Thêm thư mục gốc vào đường dẫn để import các module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.mining_tab import MiningTab
from ui.wallet_tab import WalletTab
from ui.network_tab import NetworkTab

class MainWindow:
    def __init__(self, blockchain, wallet, network):
        self.blockchain = blockchain
        self.wallet = wallet
        self.network = network
        
        self.root = tk.Tk()
        self.root.title("TuCoin Blockchain App")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Tạo menu
        self.create_menu()
        
        # Tạo notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tạo các tab
        self.wallet_tab = WalletTab(self.notebook, self.blockchain, self.wallet)
        self.mining_tab = MiningTab(self.notebook, self.blockchain, self.wallet, self.network)
        self.network_tab = NetworkTab(self.notebook, self.network)
        
        # Thêm các tab vào notebook
        self.notebook.add(self.wallet_tab.frame, text="Ví")
        self.notebook.add(self.mining_tab.frame, text="Đào Coin")
        self.notebook.add(self.network_tab.frame, text="Mạng")
        
        # Tạo thanh trạng thái
        self.status_bar = tk.Frame(self.root, height=25, bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(self.status_bar, text="Sẵn sàng")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Cập nhật trạng thái mỗi 5 giây
        self.update_status()
    
    def create_menu(self):
        """Tạo menu cho ứng dụng"""
        menubar = tk.Menu(self.root)
        
        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Tạo ví mới", command=self.create_new_wallet)
        file_menu.add_command(label="Sao lưu blockchain", command=self.backup_blockchain)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Menu Cài đặt
        settings_menu = tk.Menu(menubar, tearoff=0)
        
        # Submenu Cơ chế đồng thuận
        consensus_menu = tk.Menu(settings_menu, tearoff=0)
        self.consensus_var = tk.StringVar(value="pow")
        consensus_menu.add_radiobutton(label="Proof of Work (PoW)", 
                                      variable=self.consensus_var, 
                                      value="pow",
                                      command=self.change_consensus)
        consensus_menu.add_radiobutton(label="Proof of Stake (PoS)", 
                                      variable=self.consensus_var, 
                                      value="pos",
                                      command=self.change_consensus)
        settings_menu.add_cascade(label="Cơ chế đồng thuận", menu=consensus_menu)
        
        settings_menu.add_command(label="Cài đặt mạng", command=self.show_network_settings)
        menubar.add_cascade(label="Cài đặt", menu=settings_menu)
        
        # Menu Trợ giúp
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hướng dẫn", command=self.show_help)
        help_menu.add_command(label="Giới thiệu", command=self.show_about)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_new_wallet(self):
        """Tạo ví mới"""
        address = self.wallet.create_address()
        messagebox.showinfo("Ví mới", f"Đã tạo ví mới với địa chỉ:\n{address}")
        self.wallet_tab.update_wallet_info()
    
    def backup_blockchain(self):
        """Sao lưu blockchain"""
        try:
            self.blockchain.save_to_file()
            self.wallet.save_to_file()
            messagebox.showinfo("Sao lưu", "Đã sao lưu blockchain và ví thành công!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể sao lưu: {str(e)}")
    
    def change_consensus(self):
        """Thay đổi cơ chế đồng thuận"""
        from src.consensus import set_consensus
        
        consensus_type = self.consensus_var.get()
        try:
            set_consensus(consensus_type)
            messagebox.showinfo("Cơ chế đồng thuận", 
                               f"Đã chuyển sang cơ chế {consensus_type.upper()}")
            
            # Cập nhật tab đào coin
            self.mining_tab.update_consensus_info()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thay đổi cơ chế đồng thuận: {str(e)}")
    
    def show_network_settings(self):
        """Hiển thị cài đặt mạng"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Cài đặt mạng")
        settings_window.geometry("400x300")
        settings_window.grab_set()  # Modal window
        
        # Tạo các widget cho cài đặt mạng
        ttk.Label(settings_window, text="Cổng:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        port_entry = ttk.Entry(settings_window)
        port_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        port_entry.insert(0, str(self.network.port))
        
        ttk.Button(settings_window, text="Lưu", 
                  command=lambda: self.save_network_settings(port_entry.get(), settings_window)
                 ).grid(row=3, column=0, columnspan=2, pady=20)
    
    def save_network_settings(self, port, window):
        """Lưu cài đặt mạng"""
        try:
            port = int(port)
            if port < 1024 or port > 65535:
                raise ValueError("Cổng phải nằm trong khoảng 1024-65535")
            
            # Khởi động lại network với cổng mới
            self.network.stop_server()
            self.network.port = port
            self.network.start_server()
            
            messagebox.showinfo("Cài đặt mạng", "Đã lưu cài đặt mạng thành công!")
            window.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cài đặt: {str(e)}")
    
    def show_help(self):
        """Hiển thị hướng dẫn sử dụng"""
        help_text = """
        HƯỚNG DẪN SỬ DỤNG TUCOIN
        
        1. Tab Ví:
           - Xem số dư và địa chỉ ví
           - Gửi coin cho người khác
           - Xem lịch sử giao dịch
        
        2. Tab Đào Coin:
           - Chọn cơ chế đồng thuận (PoW hoặc PoS)
           - Bắt đầu/dừng quá trình đào
           - Xem thông tin khối đã đào
        
        3. Tab Mạng:
           - Kết nối với các node khác
           - Xem danh sách node đã kết nối
           - Tìm kiếm node trong mạng LAN
        """
        messagebox.showinfo("Hướng dẫn sử dụng", help_text)
    
    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        about_text = """
        TUCOIN BLOCKCHAIN APP
        
        Phiên bản: 1.0.0
        
        Một ứng dụng blockchain đơn giản với giao diện đồ họa,
        cho phép người dùng đào coin và kết nối với nhau trong mạng P2P.
        
        © 2023 TuCoin Team
        """
        messagebox.showinfo("Giới thiệu", about_text)
    
    def update_status(self):
        """Cập nhật thanh trạng thái"""
        # Hiển thị số khối hiện tại và số node đã kết nối
        blocks = len(self.blockchain.chain)
        nodes = len(self.network.nodes)
        
        from src.consensus import get_consensus
        consensus = get_consensus().get_name()
        
        status_text = f"Khối: {blocks} | Nodes: {nodes} | Cơ chế: {consensus}"
        self.status_label.config(text=status_text)
        
        # Lập lịch cập nhật tiếp theo
        self.root.after(5000, self.update_status)
    
    def run(self):
        """Chạy ứng dụng"""
        self.root.mainloop()