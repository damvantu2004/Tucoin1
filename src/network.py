import socket
import threading
import json
import time
import pickle
from datetime import datetime
from src.blockchain import Block

class Network:
    def __init__(self, blockchain, port=5000):
        self.blockchain = blockchain
        self.nodes = set()  # Danh sách các node đã kết nối
        self.port = port
        self.server_socket = None
        self.is_listening = False
        self.node_id = self.get_local_ip() + ":" + str(port)
    
    def get_local_ip(self):
        """
        Lấy địa chỉ IP của máy hiện tại.
        
        Returns:
            str: Địa chỉ IP
        """
        try:
            # Tạo socket để lấy địa chỉ IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start_server(self):
        """
        Khởi động server để lắng nghe kết nối từ các node khác.
        """
        if self.is_listening:
            return
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(10)
            self.is_listening = True
            
            # Bắt đầu thread lắng nghe kết nối
            threading.Thread(target=self.listen_for_connections, daemon=True).start()
            
            print(f"Server đang lắng nghe tại cổng {self.port}")
            return True
        except Exception as e:
            print(f"Không thể khởi động server: {e}")
            return False
    
    def listen_for_connections(self):
        """
        Lắng nghe kết nối từ các node khác.
        """
        while self.is_listening:
            try:
                client_socket, address = self.server_socket.accept()
                
                # Bắt đầu thread xử lý kết nối
                threading.Thread(target=self.handle_connection, args=(client_socket, address), daemon=True).start()
                
                print(f"Kết nối mới từ {address[0]}:{address[1]}")
            except Exception as e:
                if self.is_listening:
                    print(f"Lỗi khi lắng nghe kết nối: {e}")
    
    def handle_connection(self, client_socket, address):
        """
        Xử lý kết nối từ một node khác.
        
        Args:
            client_socket: Socket của client
            address: Địa chỉ của client
        """
        try:
            # Nhận dữ liệu từ client
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Kiểm tra xem đã nhận đủ dữ liệu chưa
                try:
                    message = pickle.loads(data)
                    break
                except:
                    continue
            
            if not data:
                return
            
            # Xử lý message
            self.process_message(message, client_socket)
            
        except Exception as e:
            print(f"Lỗi khi xử lý kết nối: {e}")
        finally:
            client_socket.close()
    
    def process_message(self, message, client_socket=None):
        """
        Xử lý message nhận được từ node khác.
        
        Args:
            message: Message nhận được
            client_socket: Socket của client (nếu cần phản hồi)
        """
        message_type = message.get("type")
        
        if message_type == "introduce":
            # Nhận thông tin giới thiệu từ node khác
            node_id = message.get("node_id")
            address = message.get("address")
            port = message.get("port")
            
            # Đăng ký node mới
            if node_id and node_id != self.node_id:
                self.register_node(node_id)
                
                # Gửi phản hồi xác nhận
                if client_socket:
                    response = {
                        "type": "introduce_ack",
                        "node_id": self.node_id
                    }
                    client_socket.sendall(pickle.dumps(response))
        
        elif message_type == "get_chain":
            # Gửi blockchain hiện tại
            if client_socket:
                response = {
                    "type": "chain",
                    "chain": [block.to_dict() for block in self.blockchain.chain],
                    "length": len(self.blockchain.chain)
                }
                client_socket.sendall(pickle.dumps(response))
        
        elif message_type == "chain":
            # Nhận blockchain từ node khác
            received_chain = message.get("chain")
            chain_length = message.get("length")
            
            # Kiểm tra xem chain nhận được có dài hơn không
            if chain_length > len(self.blockchain.chain):
                # Xác thực chain nhận được
                if self.validate_received_chain(received_chain):
                    print(f"Nhận chain mới hợp lệ và dài hơn ({chain_length} khối)")
                    # Chuyển đổi từ dict sang đối tượng Block
                    new_chain = []
                    for block_data in received_chain:
                        block = Block(
                            block_data["index"],
                            block_data["timestamp"],
                            block_data["transactions"],
                            block_data["previous_hash"],
                            block_data["proof"]
                        )
                        block.hash = block_data["hash"]
                        new_chain.append(block)
                    
                    # Thay thế chain hiện tại
                    self.blockchain.chain = new_chain
                    print("Đã cập nhật blockchain từ node khác")
                else:
                    print("Chain nhận được không hợp lệ, bỏ qua")
        
        elif message_type == "new_block":
            # Nhận khối mới từ node khác
            block_data = message.get("block")
            
            # Kiểm tra xem khối có phải là khối tiếp theo không
            if block_data["index"] == len(self.blockchain.chain):
                # Tạo đối tượng Block từ dữ liệu nhận được
                new_block = Block(
                    block_data["index"],
                    block_data["timestamp"],
                    block_data["transactions"],
                    block_data["previous_hash"],
                    block_data["proof"]
                )
                new_block.hash = block_data["hash"]
                
                # Xác thực khối
                if self.blockchain.is_valid_block(new_block, self.blockchain.chain[-1]):
                    # Thêm khối vào blockchain
                    self.blockchain.chain.append(new_block)
                    # Xóa các giao dịch đã được xử lý khỏi pending_transactions
                    for tx in new_block.transactions:
                        if tx in self.blockchain.pending_transactions:
                            self.blockchain.pending_transactions.remove(tx)
                    
                    print(f"Đã thêm khối mới #{new_block.index} từ node khác")
                else:
                    print(f"Khối #{block_data['index']} không hợp lệ, bỏ qua")
        
        elif message_type == "new_transaction":
            # Nhận giao dịch mới từ node khác
            transaction = message.get("transaction")
            
            # Kiểm tra xem giao dịch đã tồn tại trong pending_transactions chưa
            if transaction not in self.blockchain.pending_transactions:
                # Thêm vào pending_transactions
                self.blockchain.pending_transactions.append(transaction)
                print(f"Đã thêm giao dịch mới từ {transaction['sender']} đến {transaction['receiver']}")
        
        elif message_type == "get_nodes":
            # Gửi danh sách các node đã biết
            if client_socket:
                response = {
                    "type": "nodes",
                    "nodes": list(self.nodes)
                }
                client_socket.sendall(pickle.dumps(response))
        
        elif message_type == "nodes":
            # Nhận danh sách các node từ node khác
            received_nodes = message.get("nodes")
            if received_nodes:
                for node in received_nodes:
                    self.register_node(node)
    
    def connect_to_node(self, address, port=5000):
        """
        Kết nối đến một node khác.
        
        Args:
            address: Địa chỉ IP của node
            port: Cổng của node
            
        Returns:
            bool: True nếu kết nối thành công, False nếu không
        """
        node_address = f"{address}:{port}"
        
        if node_address in self.nodes or node_address == self.node_id:
            return True
        
        try:
            # Tạo socket và kết nối
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((address, port))
            
            # Gửi message giới thiệu về node hiện tại
            introduce_message = {
                "type": "introduce",
                "node_id": self.node_id,
                "address": self.get_local_ip(),
                "port": self.port
            }
            s.sendall(pickle.dumps(introduce_message))
            
            # Nhận phản hồi
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                try:
                    response = pickle.loads(data)
                    break
                except:
                    continue
            
            if response and response.get("type") == "introduce_ack":
                # Đăng ký node
                self.register_node(node_address)
                
                # Gửi yêu cầu lấy danh sách các node
                message = {
                    "type": "get_nodes"
                }
                s.sendall(pickle.dumps(message))
                
                # Nhận phản hồi
                data = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    
                    try:
                        response = pickle.loads(data)
                        break
                    except:
                        continue
                
                # Xử lý phản hồi
                if response and response.get("type") == "nodes":
                    self.process_message(response)
                
                s.close()
                return True
            
            s.close()
            return False
        except Exception as e:
            print(f"Không thể kết nối đến {address}:{port}: {e}")
            return False
    
    def register_node(self, node_address):
        """
        Đăng ký một node mới.
        
        Args:
            node_address: Địa chỉ của node (dạng "ip:port")
        """
        if node_address != self.node_id:
            self.nodes.add(node_address)
    
    def broadcast_block(self, block):
        """
        Gửi khối mới đến tất cả các node đã kết nối.
        
        Args:
            block: Khối cần gửi
        """
        message = {
            "type": "new_block",
            "block": block.to_dict()
        }
        
        self.broadcast_message(message)
    
    def broadcast_transaction(self, transaction):
        """
        Gửi giao dịch mới đến tất cả các node đã kết nối.
        
        Args:
            transaction: Giao dịch cần gửi
        """
        message = {
            "type": "new_transaction",
            "transaction": transaction
        }
        
        self.broadcast_message(message)
    
    def broadcast_message(self, message):
        """
        Gửi message đến tất cả các node đã kết nối.
        
        Args:
            message: Message cần gửi
        """
        for node in self.nodes:
            try:
                # Tách địa chỉ và cổng
                address, port = node.split(":")
                port = int(port)
                
                # Tạo socket và kết nối
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((address, port))
                
                # Gửi message
                s.sendall(pickle.dumps(message))
                
                s.close()
            except Exception as e:
                print(f"Không thể gửi message đến {node}: {e}")
    
    def discover_nodes(self):
        """
        Tìm kiếm các node trong mạng LAN.
        """
        # Lấy địa chỉ IP của mạng LAN
        ip_parts = self.get_local_ip().split('.')
        network_prefix = '.'.join(ip_parts[:3])
        
        # Quét các địa chỉ IP trong mạng LAN
        for i in range(1, 255):
            ip = f"{network_prefix}.{i}"
            
            # Bỏ qua địa chỉ IP của chính mình
            if ip == self.get_local_ip():
                continue
            
            # Thử kết nối đến node
            threading.Thread(target=self.connect_to_node, args=(ip, self.port), daemon=True).start()
    
    def validate_received_chain(self, chain):
        """
        Xác thực một blockchain nhận được từ node khác.
        
        Args:
            chain: Blockchain cần xác thực (dạng list các dict)
            
        Returns:
            bool: True nếu chain hợp lệ, False nếu không
        """
        # Kiểm tra xem chain có rỗng không
        if not chain:
            return False
        
        # Kiểm tra khối genesis
        if chain[0]["index"] != 0:
            return False
        
        # Kiểm tra tính liên tục và hash của các khối
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            
            # Kiểm tra index
            if current["index"] != previous["index"] + 1:
                return False
            
            # Kiểm tra liên kết với khối trước
            if current["previous_hash"] != previous["hash"]:
                return False
            
            # Tạo đối tượng Block để tính toán hash
            from datetime import datetime
            block = Block(
                current["index"],
                current["timestamp"],
                current["transactions"],
                current["previous_hash"],
                current["proof"]
            )
            
            # Kiểm tra hash của khối
            if block.calculate_hash() != current["hash"]:
                return False
        
        return True
    
    def stop_server(self):
        """
        Dừng server.
        """
        self.is_listening = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

