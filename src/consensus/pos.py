import hashlib
import json
import random
from datetime import datetime
from .base import ConsensusAlgorithm
from ..blockchain import Block

class ProofOfStake(ConsensusAlgorithm):
    """
    Triển khai cơ chế đồng thuận Proof of Stake.
    """
    
    def __init__(self, min_stake=100):
        """
        Khởi tạo cơ chế Proof of Stake.
        
        Args:
            min_stake: Số lượng coin tối thiểu để tham gia stake
        """
        self.min_stake = min_stake
        self.stakes = {}  # {address: staked_amount}
        self.difficulty = 1  # Độ khó cho PoS (ít quan trọng hơn PoW)
    
    def get_name(self):
        return "Proof of Stake"
    
    def get_difficulty(self):
        return self.difficulty
    
    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
    
    def add_stake(self, address, amount):
        """
        Thêm stake cho một địa chỉ.
        
        Args:
            address: Địa chỉ ví
            amount: Số lượng coin stake
        """
        if address in self.stakes:
            self.stakes[address] += amount
        else:
            self.stakes[address] = amount
    
    def remove_stake(self, address, amount):
        """
        Giảm stake của một địa chỉ.
        
        Args:
            address: Địa chỉ ví
            amount: Số lượng coin rút
        """
        if address in self.stakes and self.stakes[address] >= amount:
            self.stakes[address] -= amount
            if self.stakes[address] == 0:
                del self.stakes[address]
            return True
        return False
    
    def get_stake(self, address):
        """
        Lấy số lượng coin đã stake của một địa chỉ.
        
        Args:
            address: Địa chỉ ví
            
        Returns:
            float: Số lượng coin đã stake
        """
        return self.stakes.get(address, 0)
    
    def select_validator(self):
        """
        Chọn validator dựa trên số lượng coin đã stake.
        
        Returns:
            str: Địa chỉ của validator được chọn
        """
        if not self.stakes:
            return None
        
        # Lọc các địa chỉ có stake >= min_stake
        eligible_stakers = {addr: amount for addr, amount in self.stakes.items() 
                           if amount >= self.min_stake}
        
        if not eligible_stakers:
            return None
        
        # Tính tổng stake
        total_stake = sum(eligible_stakers.values())
        
        # Chọn validator dựa trên xác suất tỷ lệ với số lượng stake
        selection_point = random.uniform(0, total_stake)
        current_sum = 0
        
        for address, stake in eligible_stakers.items():
            current_sum += stake
            if current_sum >= selection_point:
                return address
        
        # Fallback nếu có lỗi
        return list(eligible_stakers.keys())[0]
    
    def mine(self, blockchain, miner_address):
        """
        Tạo khối mới sử dụng Proof of Stake.
        
        Args:
            blockchain: Đối tượng blockchain hiện tại
            miner_address: Địa chỉ của người đào để nhận phần thưởng
            
        Returns:
            Block: Khối mới được tạo
        """
        # Kiểm tra xem miner có đủ stake không
        if self.get_stake(miner_address) < self.min_stake:
            raise ValueError(f"Địa chỉ {miner_address} không có đủ stake (tối thiểu {self.min_stake})")
        
        # Chọn validator
        validator = self.select_validator()
        
        # Nếu miner không phải là validator được chọn
        if validator != miner_address:
            raise ValueError(f"Địa chỉ {miner_address} không được chọn làm validator")
        
        # Thêm giao dịch thưởng cho validator (phần thưởng nhỏ hơn PoW)
        blockchain.add_transaction("0", validator, 10)
        
        last_block = blockchain.get_last_block()
        
        # Chuẩn bị dữ liệu cho khối mới
        index = last_block.index + 1
        timestamp = datetime.now()
        transactions = blockchain.pending_transactions.copy()
        previous_hash = last_block.hash
        
        # Trong PoS, proof là địa chỉ của validator
        proof = validator
        
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
        
        # Kiểm tra validator có đủ stake không
        validator = block.proof
        if self.get_stake(validator) < self.min_stake:
            return False
        
        return True