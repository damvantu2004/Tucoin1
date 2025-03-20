import hashlib
import json
import os
import random
import string
from datetime import datetime

class Wallet:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.addresses = {}  # {address: private_key}
        self.current_address = None
    
    def create_address(self):
        """
        Tạo một địa chỉ ví mới.
        
        Returns:
            str: Địa chỉ ví mới
        """
        # Tạo private key đơn giản (trong thực tế cần dùng cryptography)
        private_key = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        
        # Tạo địa chỉ từ private key
        address = hashlib.sha256(private_key.encode()).hexdigest()[:40]
        
        self.addresses[address] = private_key
        
        if not self.current_address:
            self.current_address = address
        
        return address
    
    def get_balance(self, address=None):
        """
        Lấy số dư của một địa chỉ.
        
        Args:
            address: Địa chỉ ví (nếu None thì dùng địa chỉ hiện tại)
            
        Returns:
            float: Số dư của địa chỉ
        """
        if address is None:
            address = self.current_address
        
        if not address:
            return 0
        
        balance = 0
        
        # Duyệt qua tất cả các khối
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx["receiver"] == address:
                    balance += tx["amount"]
                if tx["sender"] == address:
                    balance -= tx["amount"]
        
        # Kiểm tra cả giao dịch đang chờ
        for tx in self.blockchain.pending_transactions:
            if tx["receiver"] == address:
                balance += tx["amount"]
            if tx["sender"] == address:
                balance -= tx["amount"]
        
        return balance
    
    def send(self, receiver, amount):
        """
        Gửi coin từ địa chỉ hiện tại đến địa chỉ khác.
        
        Args:
            receiver: Địa chỉ người nhận
            amount: Số lượng coin gửi
            
        Returns:
            bool: True nếu giao dịch thành công, False nếu không
        """
        if not self.current_address:
            return False
        
        balance = self.get_balance()
        
        if balance < amount:
            return False
        
        # Thêm giao dịch vào blockchain
        self.blockchain.add_transaction(self.current_address, receiver, amount)
        
        return True
    
    def get_transaction_history(self, address=None):
        """
        Lấy lịch sử giao dịch của một địa chỉ.
        
        Args:
            address: Địa chỉ ví (nếu None thì dùng địa chỉ hiện tại)
            
        Returns:
            list: Danh sách các giao dịch
        """
        if address is None:
            address = self.current_address
        
        if not address:
            return []
        
        transactions = []
        
        # Duyệt qua tất cả các khối
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx["sender"] == address or tx["receiver"] == address:
                    tx_copy = tx.copy()
                    tx_copy["block_index"] = block.index
                    tx_copy["confirmed"] = True
                    transactions.append(tx_copy)
        
        # Thêm giao dịch đang chờ
        for tx in self.blockchain.pending_transactions:
            if tx["sender"] == address or tx["receiver"] == address:
                tx_copy = tx.copy()
                tx_copy["confirmed"] = False
                transactions.append(tx_copy)
        
        # Sắp xếp theo thời gian
        transactions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return transactions
    
    def save_to_file(self, filename="data/wallet.json"):
        """
        Lưu ví vào file.
        
        Args:
            filename: Đường dẫn file
        """
        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        data = {
            "addresses": self.addresses,
            "current_address": self.current_address
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_file(self, filename="data/wallet.json"):
        """
        Tải ví từ file.
        
        Args:
            filename: Đường dẫn file
            
        Returns:
            bool: True nếu tải thành công, False nếu không
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.addresses = data["addresses"]
            self.current_address = data["current_address"]
            
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            # Nếu file không tồn tại hoặc không hợp lệ, tạo ví mới
            self.create_address()
            self.save_to_file(filename)
            return False