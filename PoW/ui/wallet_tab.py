import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

class WalletTab:
    def __init__(self, parent, blockchain, wallet):
        self.parent = parent
        self.blockchain = blockchain
        self.wallet = wallet
        
        self.frame = ttk.Frame(parent)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các widget cho tab ví"""
        # Frame thông tin ví
        wallet_info_frame = ttk.LabelFrame(self.frame, text="Thông tin ví")
        wallet_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Địa chỉ ví
        ttk.Label(wallet_info_frame, text="Địa chỉ ví:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.wallet_var = tk.StringVar()
        self.wallet_combo = ttk.Combobox(wallet_info_frame, textvariable=self.wallet_var, width=50)
        self.wallet_combo.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        self.wallet_combo.bind("<<ComboboxSelected>>", self.on_wallet_selected)
        
        # Nút tạo ví mới
        ttk.Button(wallet_info_frame, text="Tạo ví mới", command=self.create_new_wallet).grid(
            row=0, column=2, padx=10, pady=5)
        
        # Số dư
        ttk.Label(wallet_info_frame, text="Số dư:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.balance_label = ttk.Label(wallet_info_frame, text="0 TuCoin")
        self.balance_label.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Nút làm mới
        ttk.Button(wallet_info_frame, text="Làm mới", command=self.update_wallet_info).grid(
            row=1, column=2, padx=10, pady=5)
        
        # Frame gửi coin
        send_frame = ttk.LabelFrame(self.frame, text="Gửi TuCoin")
        send_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Địa chỉ người nhận
        ttk.Label(send_frame, text="Địa chỉ người nhận:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.receiver_entry = ttk.Entry(send_frame, width=50)
        self.receiver_entry.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Số lượng
        ttk.Label(send_frame, text="Số lượng:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.amount_entry = ttk.Entry(send_frame)
        self.amount_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Nút gửi
        ttk.Button(send_frame, text="Gửi", command=self.send_coins).grid(
            row=2, column=0, columnspan=2, padx=10, pady=10)
        
        # Frame lịch sử giao dịch
        history_frame = ttk.LabelFrame(self.frame, text="Lịch sử giao dịch")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview để hiển thị lịch sử giao dịch
        columns = ("timestamp", "type", "address", "amount", "status")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        # Định nghĩa các cột
        self.history_tree.heading("timestamp", text="Thời gian")
        self.history_tree.heading("type", text="Loại")
        self.history_tree.heading("address", text="Địa chỉ")
        self.history_tree.heading("amount", text="Số lượng")
        self.history_tree.heading("status", text="Trạng thái")
        
        # Thiết lập độ rộng cột
        self.history_tree.column("timestamp", width=150)
        self.history_tree.column("type", width=100)
        self.history_tree.column("address", width=300)
        self.history_tree.column("amount", width=100)
        self.history_tree.column("status", width=100)
        
        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        
        # Pack các widget
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cập nhật thông tin ví
        self.update_wallet_addresses()
        self.update_wallet_info()
    
    def update_wallet_addresses(self):
        """Cập nhật danh sách địa chỉ ví"""
        addresses = list(self.wallet.addresses.keys())
        self.wallet_combo['values'] = addresses
        
        if addresses and self.wallet.current_address:
            self.wallet_var.set(self.wallet.current_address)
    
    def on_wallet_selected(self, event):
        """Xử lý sự kiện khi chọn ví"""
        selected_address = self.wallet_var.get()
        if selected_address:
            self.wallet.current_address = selected_address
            self.update_wallet_info()
    
    def create_new_wallet(self):
        """Tạo ví mới"""
        address = self.wallet.create_address()
        messagebox.showinfo("Ví mới", f"Đã tạo ví mới với địa chỉ:\n{address}")
        
        # Cập nhật danh sách địa chỉ và thông tin ví
        self.update_wallet_addresses()
        self.update_wallet_info()
        
        # Lưu ví
        self.wallet.save_to_file()
    
    def update_wallet_info(self):
        """Cập nhật thông tin ví"""
        # Cập nhật số dư
        if self.wallet.current_address:
            balance = self.wallet.get_balance()
            self.balance_label.config(text=f"{balance} TuCoin")
        
        # Cập nhật lịch sử giao dịch
        self.update_transaction_history()
    
    def update_transaction_history(self):
        """Cập nhật lịch sử giao dịch"""
        # Xóa dữ liệu cũ
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Lấy lịch sử giao dịch
        if not self.wallet.current_address:
            return
            
        transactions = self.wallet.get_transaction_history()
        
        # Thêm vào treeview
        for tx in transactions:
            # Xác định loại giao dịch và địa chỉ hiển thị
            if tx["sender"] == "0":
                tx_type = "Đào coin"
                address = "Hệ thống"
                amount = f"+{tx['amount']}"
            elif tx["sender"] == self.wallet.current_address:
                tx_type = "Gửi"
                address = tx["receiver"]
                amount = f"-{tx['amount']}"
            else:
                tx_type = "Nhận"
                address = tx["sender"]
                amount = f"+{tx['amount']}"
            
            # Xác định trạng thái
            status = "Đã xác nhận" if tx.get("confirmed", False) else "Đang chờ"
            
            # Chuyển đổi timestamp
            try:
                timestamp = datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00"))
                timestamp_str = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            except:
                timestamp_str = tx["timestamp"]
            
            # Thêm vào treeview
            self.history_tree.insert("", tk.END, values=(timestamp_str, tx_type, address, amount, status))
    
    def send_coins(self):
        """Gửi coin cho người khác"""
        # Kiểm tra xem đã chọn ví chưa
        if not self.wallet.current_address:
            messagebox.showerror("Lỗi", "Vui lòng chọn ví để g��i coin")
            return
        
        # Lấy thông tin giao dịch
        receiver = self.receiver_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        
        # Kiểm tra dữ liệu đầu vào
        if not receiver:
            messagebox.showerror("Lỗi", "Vui lòng nhập địa chỉ người nhận")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Số lượng phải lớn hơn 0")
        except ValueError:
            messagebox.showerror("Lỗi", "Số lượng không hợp lệ")
            return
        
        # Kiểm tra số dư
        balance = self.wallet.get_balance()
        if balance < amount:
            messagebox.showerror("Lỗi", f"Số dư không đủ. Bạn chỉ có {balance} TuCoin")
            return
        
        # Gửi coin
        if self.wallet.send(receiver, amount):
            messagebox.showinfo("Thành công", f"Đã gửi {amount} TuCoin đến {receiver}")
            
            # Xóa dữ liệu đã nhập
            self.receiver_entry.delete(0, tk.END)
            self.amount_entry.delete(0, tk.END)
            
            # Cập nhật thông tin ví
            self.update_wallet_info()
            
            # Lưu blockchain
            self.blockchain.save_to_file()
            
            # Broadcast giao dịch (nếu có network)
            if hasattr(self, 'network') and self.network:
                latest_tx = self.blockchain.pending_transactions[-1]
                self.network.broadcast_transaction(latest_tx)
        else:
            messagebox.showerror("Lỗi", "Không thể gửi coin. Vui lòng thử lại sau")