import hashlib
import json
from datetime import datetime
from .base import ConsensusAlgorithm
from ..blockchain import Block

class ProofOfWork(ConsensusAlgorithm):
    """
    Triển khai cơ chế đồng thuận Proof of Work.
    """
    
    def __init__(self, difficulty=4):
        """
        Khởi tạo cơ chế Proof of Work.
        
        Args:
            difficulty: Số lượng số 0 đứng đầu chuỗi hash
        """
        self.difficulty = difficulty
        self.target = '0' * difficulty
    
    def get_name(self):
        return "Proof of Work"
    
    def get_difficulty(self):
        return self.difficulty
    
    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.target = '0' * difficulty
    
    def calculate_hash(self, index, timestamp, transactions, previous_hash, proof):
        """
        Tính toán hash của một khối với nonce cụ thể.
        
        Returns:
            str: Chuỗi hash của khối
        """
        block_string = json.dumps({
            "index": index,
            "timestamp": str(timestamp),
            "transactions": transactions,
            "previous_hash": previous_hash,
            "proof": proof
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def proof_of_work(self, index, timestamp, transactions, previous_hash):
        """
        Thực hiện thuật toán Proof of Work để tìm nonce hợp lệ.
        
        Returns:
            int: Giá trị nonce tìm được
        """
        proof = 0
        while True:
            hash = self.calculate_hash(index, timestamp, transactions, previous_hash, proof)
            if hash.startswith(self.target):
                return proof
            proof += 1
    
    def mine(self, blockchain, miner_address):
        """
        Đào một khối mới sử dụng Proof of Work.
        
        Args:
            blockchain: Đối tượng blockchain hiện tại
            miner_address: Địa chỉ của người đào để nhận phần thưởng
            
        Returns:
            Block: Khối mới được đào
        """
        # Thêm giao dịch thưởng cho người đào
        blockchain.add_transaction("0", miner_address, 100)
        
        last_block = blockchain.get_last_block()
        
        # Chuẩn bị dữ liệu cho khối mới
        index = last_block.index + 1
        timestamp = datetime.now()
        transactions = blockchain.pending_transactions.copy()
        previous_hash = last_block.hash
        
        # Tìm proof hợp lệ
        proof = self.proof_of_work(index, timestamp, transactions, previous_hash)
        
        # Tạo khối mới
        block = Block(index, timestamp, transactions, previous_hash, proof)
        
        # Reset danh sách giao dịch đang chờ
        blockchain.pending_transactions = []
        blockchain.chain.append(block)
        
        return block
    
    def validate_block(self, block, blockchain):
        """
        Xác thực một khối mới.
        
        Args:
            block: Khối cần xác thực
            blockchain: Đối tượng blockchain hiện tại
            
        Returns:
            bool: True nếu khối hợp lệ, False nếu không
        """
        # Kiểm tra hash của khối
        if block.hash != block.calculate_hash():
            return False
        
        # Kiểm tra liên kết với khối trước
        if block.previous_hash != blockchain.chain[-1].hash:
            return False
        
        # Kiểm tra proof of work
        hash = self.calculate_hash(
            block.index, 
            block.timestamp, 
            block.transactions, 
            block.previous_hash, 
            block.proof
        )
        
        return hash.startswith(self.target)