import hashlib
import json
import time
from datetime import datetime

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, proof=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.proof = proof
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": str(self.timestamp),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "proof": self.proof
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": str(self.timestamp),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "proof": self.proof,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.nodes = set()
        
        # Tạo khối genesis
        self.create_genesis_block()
    
    def create_genesis_block(self):
        genesis_block = Block(0, datetime.now(), [], "0", 0)
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
    
    def get_last_block(self):
        return self.chain[-1]
    
    def add_transaction(self, sender, receiver, amount):
        self.pending_transactions.append({
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "timestamp": str(datetime.now())
        })
        return self.get_last_block().index + 1
    
    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
    
    def valid_proof(self, last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    
    def mine_block(self, miner_address):
        # Thêm giao dịch thưởng cho người đào
        self.add_transaction("0", miner_address, 100)
        
        last_block = self.get_last_block()
        last_proof = last_block.proof
        proof = self.proof_of_work(last_proof)
        
        previous_hash = last_block.hash
        block = Block(
            index=last_block.index + 1,
            timestamp=datetime.now(),
            transactions=self.pending_transactions,
            previous_hash=previous_hash,
            proof=proof
        )
        
        # Reset danh sách giao dịch đang chờ
        self.pending_transactions = []
        self.chain.append(block)
        return block
    
    def is_valid_block(self, block, previous_block):
        """
        Xác thực một khối mới.
        
        Args:
            block: Khối cần xác thực
            previous_block: Khối trước đó
            
        Returns:
            bool: True nếu khối hợp lệ, False nếu không
        """
        # Kiểm tra index
        if block.index != previous_block.index + 1:
            return False
        
        # Kiểm tra liên kết với khối trước
        if block.previous_hash != previous_block.hash:
            return False
        
        # Kiểm tra hash của khối
        if block.hash != block.calculate_hash():
            return False
        
        # Kiểm tra proof of work
        if not self.valid_proof(previous_block.proof, block.proof):
            return False
        
        return True
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            if not self.is_valid_block(current, previous):
                return False
        
        return True
    
    def save_to_file(self, filename="data/blockchain.json"):
        data = {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": self.pending_transactions
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_file(self, filename="data/blockchain.json"):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self.chain = []
            for block_data in data["chain"]:
                block = Block(
                    block_data["index"],
                    block_data["timestamp"],
                    block_data["transactions"],
                    block_data["previous_hash"],
                    block_data["proof"]
                )
                block.hash = block_data["hash"]
                self.chain.append(block)
                
            self.pending_transactions = data["pending_transactions"]
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False
