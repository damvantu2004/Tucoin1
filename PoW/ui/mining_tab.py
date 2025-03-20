import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

from src.consensus import get_consensus

class MiningTab:
    def __init__(self, parent, blockchain, wallet, network):
        self.parent = parent
        self.blockchain = blockchain
        self.wallet = wallet
        self.network = network
        
        self.frame = ttk.Frame(parent)
        self.mining_thread = None
        self.is_mining = False
        
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các widget cho tab đào coin"""
        # Frame thông tin
        info_frame = ttk.LabelFrame(self.frame, text="Thông tin đào coin")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Thông tin cơ chế đồng thuận
        ttk.Label(info_frame, text="Cơ chế đồng thuận:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.consensus_label = ttk.Label(info_frame, text="Proof of Work")
        self.consensus_label.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Thông tin độ khó
        ttk.Label(info_frame, text="Độ khó:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.difficulty_label = ttk.Label(info_frame, text="4")
        self.difficulty_label.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Thông tin khối hiện tại
        ttk.Label(info_frame, text="Khối hiện tại:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.current_block_label = ttk.Label(info_frame, text="0")
        self.current_block_label.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Frame cài đặt đào
        mining_frame = ttk.LabelFrame(self.frame, text="Cài đặt đào")
        mining_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Địa chỉ ví nhận thưởng
        ttk.Label(mining_frame, text="Địa chỉ ví:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.wallet_var = tk.StringVar()
        self.wallet_combo = ttk.Combobox(mining_frame, textvariable=self.wallet_var, width=50)
        self.wallet_combo.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        self.update_wallet_addresses()
        
        # Nút đào/dừng
        self.mining_button = ttk.Button(mining_frame, text="Bắt đầu đào", command=self.toggle_mining)
        self.mining_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        
        # Frame log
        log_frame = ttk.LabelFrame(self.frame, text="Log đào coin")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text widget để hiển thị log
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar cho text widget
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Cập nhật thông tin
        self.update_consensus_info()
        self.update_blockchain_info()
    
    def update_wallet_addresses(self):
        """Cập nhật danh sách địa chỉ ví"""
        addresses = list(self.wallet.addresses.keys())
        self.wallet_combo['values'] = addresses
        
        if addresses and self.wallet.current_address:
            self.wallet_var.set(self.wallet.current_address)
    
    def update_consensus_info(self):
        """Cập nhật thông tin cơ chế đồng thuận"""
        consensus = get_consensus()
        self.consensus_label.config(text=consensus.get_name())
        self.difficulty_label.config(text=str(consensus.get_difficulty()))
    
    def update_blockchain_info(self):
        """Cập nhật thông tin blockchain"""
        current_block = len(self.blockchain.chain) - 1
        self.current_block_label.config(text=str(current_block))
    
    def toggle_mining(self):
        """Bắt đầu hoặc dừng quá trình đào"""
        if self.is_mining:
            self.stop_mining()
        else:
            self.start_mining()
    
    def start_mining(self):
        """Bắt đầu quá trình đào"""
        # Kiểm tra xem đã chọn địa chỉ ví chưa
        wallet_address = self.wallet_var.get()
        if not wallet_address:
            messagebox.showerror("Lỗi", "Vui lòng chọn địa chỉ ví để nhận thưởng")
            return
        
        # Kiểm tra xem địa chỉ ví có hợp lệ không
        if wallet_address not in self.wallet.addresses:
            messagebox.showerror("Lỗi", "Địa chỉ ví không hợp lệ")
            return
        
        # Kiểm tra cơ chế đồng thuận
        consensus = get_consensus()
        if consensus.get_name() == "Proof of Stake":
            # Kiểm tra xem có đủ stake không
            stake = consensus.get_stake(wallet_address)
            min_stake = consensus.min_stake
            if stake < min_stake:
                messagebox.showerror("Lỗi", 
                                    f"Bạn cần có ít nhất {min_stake} TuCoin để tham gia Proof of Stake.\n"
                                    f"Số dư hiện tại: {stake} TuCoin")
                return
        
        # Bắt đầu thread đào
        self.is_mining = True
        self.mining_button.config(text="Dừng đào")
        self.log("Bắt đầu quá trình đào...")
        
        self.mining_thread = threading.Thread(target=self.mining_process, args=(wallet_address,))
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def stop_mining(self):
        """Dừng quá trình đào"""
        self.is_mining = False
        self.mining_button.config(text="Bắt đầu đào")
        self.log("Đã dừng quá trình đào.")
    
    def mining_process(self, wallet_address):
        """Quá trình đào coin"""
        consensus = get_consensus()
        
        while self.is_mining:
            try:
                # Đào kh��i mới
                self.log(f"Đang đào khối mới với cơ chế {consensus.get_name()}...")
                start_time = time.time()
                
                # Đào khối
                new_block = consensus.mine(self.blockchain, wallet_address)
                
                # Tính thời gian đào
                mining_time = time.time() - start_time
                
                # Log thông tin
                self.log(f"Đã đào thành công khối #{new_block.index}!")
                self.log(f"Hash: {new_block.hash[:20]}...")
                self.log(f"Thời gian: {mining_time:.2f} giây")
                self.log(f"Phần thưởng: 100 TuCoin")
                
                # Cập nhật thông tin blockchain
                self.update_blockchain_info()
                
                # Lưu blockchain
                self.blockchain.save_to_file()
                
                # Broadcast khối mới
                self.network.broadcast_block(new_block)
                
                # Nghỉ một chút trước khi đào tiếp
                time.sleep(1)
            except Exception as e:
                self.log(f"Lỗi khi đào: {str(e)}")
                time.sleep(5)  # Nghỉ lâu hơn nếu có lỗi
    
    def log(self, message):
        """Thêm message vào log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Thêm vào cuối và scroll xuống
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)