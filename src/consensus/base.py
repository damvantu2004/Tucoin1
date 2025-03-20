from abc import ABC, abstractmethod

class ConsensusAlgorithm(ABC):
    """
    Interface chung cho các cơ chế đồng thuận.
    Các lớp con phải triển khai các phương thức này.
    """
    
    @abstractmethod
    def mine(self, blockchain, miner_address):
        """
        Đào một khối mới và thêm vào blockchain.
        
        Args:
            blockchain: Đối tượng blockchain hiện tại
            miner_address: Địa chỉ của người đào để nhận phần thưởng
            
        Returns:
            Block: Khối mới được đào
        """
        pass
    
    @abstractmethod
    def validate_block(self, block, blockchain):
        """
        Xác thực một khối mới.
        
        Args:
            block: Khối cần xác thực
            blockchain: Đối tượng blockchain hiện tại
            
        Returns:
            bool: True nếu khối hợp lệ, False nếu không
        """
        pass
    
    @abstractmethod
    def get_name(self):
        """
        Trả về tên của cơ chế đồng thuận.
        
        Returns:
            str: Tên của cơ chế đồng thuận
        """
        pass
    
    @abstractmethod
    def get_difficulty(self):
        """
        Trả về độ khó hiện tại của cơ chế đồng thuận.
        
        Returns:
            int: Độ khó hiện tại
        """
        pass
    
    @abstractmethod
    def set_difficulty(self, difficulty):
        """
        Thiết lập độ khó cho cơ chế đồng thuận.
        
        Args:
            difficulty: Độ khó mới
        """
        pass