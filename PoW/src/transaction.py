import time
import json
import hashlib

class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = time.time()
        self.signature = None
    
    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature
        }
    
    def calculate_hash(self):
        transaction_string = json.dumps({
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp
        }, sort_keys=True).encode()
        
        return hashlib.sha256(transaction_string).hexdigest()
    
    def sign_transaction(self, private_key):
        # Đơn giản hóa: trong thực tế cần dùng cryptography để ký
        self.signature = hashlib.sha256(
            (private_key + self.calculate_hash()).encode()
        ).hexdigest()
    
    def is_valid(self):
        # Giao dịch từ hệ thống (phần thưởng) không cần chữ ký
        if self.sender == "0":
            return True
            
        if not self.signature:
            return False
            
        # Trong thực tế cần xác minh chữ ký với khóa công khai
        return True