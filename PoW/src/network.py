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
        self.node_id = f"{self.get_local_ip()}:{port}"  # ID của node hiện tại
        self.discovery_port = 5500  # Port riêng cho node discovery
        self.is_discovering = False
        self.active_connections = {}  # Lưu các kết nối đang active
        self.discovery_socket = None
        self.broadcast_socket = None
        self._lock = threading.Lock()
        
        # Thêm callbacks cho các event
        self.callbacks = {
            'new_transaction': [],
            'new_block': [],
            'new_node': [],
            'chain_updated': [],
            'connection_error': [],
            'sync_started': [],    # Thêm callback mới
            'sync_completed': [],  # Thêm callback mới
            'sync_failed': [],     # Thêm callback mới
            'node_offline': [],    # Callback khi node offline
            'node_online': []      # Callback khi node online trở lại
        }

        self.heartbeat_interval = 30  # Gửi heartbeat mỗi 30 giây
        self.node_last_seen = {}  # Lưu thời gian cuối cùng nhận được heartbeat
        self.offline_threshold = 7  # Node được coi là offline sau 90 giây không phản hồi

    def add_callback(self, event_type, callback):
        """
        Đăng ký callback cho một event
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    def notify(self, event_type, data):
        """
        Gọi tất cả callbacks đã đăng ký cho một event
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                callback(data)
    
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
        
        if message_type == "heartbeat":
            self.handle_heartbeat(message)
            return
        
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
                self.notify('new_node', {
                    'node_id': node_id,
                    'address': address,
                    'port': port
                })
        
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
            
            if chain_length > len(self.blockchain.chain):
                # Thông báo bắt đầu đồng bộ
                self.notify('sync_started', {
                    'current_length': len(self.blockchain.chain),
                    'target_length': chain_length
                })
                
                try:
                    if self.validate_received_chain(received_chain):
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
                        
                        self.blockchain.chain = new_chain
                        print("Đã cập nhật blockchain từ node khác")
                        
                        # Thông báo đồng bộ thành công
                        self.notify('sync_completed', {
                            'new_length': chain_length,
                            'blocks_synced': chain_length - len(self.blockchain.chain)
                        })
                    else:
                        print("Chain nhận được không hợp lệ, bỏ qua")
                        # Thông báo đồng bộ thất bại
                        self.notify('sync_failed', {
                            'reason': 'invalid_chain',
                            'current_length': len(self.blockchain.chain)
                        })
                except Exception as e:
                    print(f"Lỗi khi đồng bộ chain: {e}")
                    self.notify('sync_failed', {
                        'reason': str(e),
                        'current_length': len(self.blockchain.chain)
                    })
        
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
                    self.notify('new_block', {
                        'block': new_block,
                        'from_node': message.get("sender_node_id")
                    })
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
                self.notify('new_transaction', {
                    'transaction': transaction,
                    'from_node': message.get("sender_node_id")
                })
        
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
        
        elif message_type == "node_status":
            # Nhận thông báo về trạng thái node từ node khác
            node_id = message.get("node_id")
            status = message.get("status")
            if node_id != self.node_id:
                if status == "offline":
                    with self._lock:
                        if node_id in self.nodes:
                            self.nodes.remove(node_id)
                            if node_id in self.active_connections:
                                self.active_connections[node_id].close()
                                del self.active_connections[node_id]
                            self.notify('node_offline', {'node_id': node_id})
                elif status == "online":
                    with self._lock:
                        if node_id not in self.nodes:
                            self.nodes.add(node_id)
                            self.notify('node_online', {'node_id': node_id})
            return

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

    def start_discovery_service(self):
        """Khởi động service phát hiện node"""
        if self.is_discovering:
            return
            
        self.is_discovering = True
        print("Bắt đầu dịch vụ discovery...")
        
        # Khởi tạo discovery socket
        self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.discovery_socket.bind(('', self.discovery_port))
        
        # Khởi tạo broadcast socket
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Start discovery threads
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.listen_for_presence, daemon=True).start()

    def broadcast_presence(self):
        """Gửi broadcast để thông báo sự hiện diện"""
        while self.is_discovering and self.broadcast_socket:
            try:
                announcement = {
                    "type": "node_announcement",
                    "node_id": self.node_id,
                    "port": self.port
                }
                
                self.broadcast_socket.sendto(
                    json.dumps(announcement).encode(),
                    ('255.255.255.255', self.discovery_port)
                )
            except Exception as e:
                if self.is_discovering:
                    print(f"Lỗi khi gửi broadcast: {e}")
            time.sleep(5)  # Giảm tần suất broadcast

    def listen_for_presence(self):
        """Lắng nghe các announcement từ node khác"""
        while self.is_discovering and self.discovery_socket:
            try:
                data, addr = self.discovery_socket.recvfrom(1024)
                announcement = json.loads(data.decode())
                
                if announcement["type"] == "node_announcement":
                    remote_node_id = announcement["node_id"]
                    remote_port = announcement["port"]
                    
                    if remote_node_id != self.node_id:
                        node_address = f"{addr[0]}:{remote_port}"
                        
                        # Chỉ kết nối nếu chưa có kết nối
                        with self._lock:
                            if node_address not in self.nodes:
                                self.connect_to_node(addr[0], remote_port)
                        
            except Exception as e:
                if self.is_discovering:
                    print(f"Lỗi khi xử lý announcement: {e}")

    def discover_nodes(self):
        """Bắt đầu quá trình tìm kiếm node"""
        if not self.is_discovering:
            self.start_discovery_service()

    def handle_node_messages(self, node_address, sock):
        """Xử lý messages từ một node đã kết nối"""
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                    
                message = pickle.loads(data)
                self.process_message(message)
                
        except Exception as e:
            print(f"Lỗi khi xử lý messages từ {node_address}: {e}")
        finally:
            # Cleanup khi mất kết nối
            sock.close()
            self.nodes.remove(node_address)
            del self.active_connections[node_address]
            print(f"Đã ngắt kết nối với {node_address}")

    def stop_discovery(self):
        """Dừng dịch vụ discovery"""
        self.is_discovering = False
        print("Đã dừng dịch vụ discovery")

    def cleanup(self):
        """Dọn dẹp tài nguyên khi đóng ứng dụng"""
        print("Đang dọn dẹp tài nguyên mạng...")
        
        # Stop discovery service
        self.is_discovering = False
        
        # Close discovery sockets
        if self.discovery_socket:
            self.discovery_socket.close()
        if self.broadcast_socket:
            self.broadcast_socket.close()
            
        # Close all connections
        with self._lock:
            for sock in self.active_connections.values():
                try:
                    sock.close()
                except:
                    pass
            self.active_connections.clear()
            self.nodes.clear()
        
        # Close server socket
        if self.server_socket:
            self.is_listening = False
            try:
                self.server_socket.close()
            except:
                pass
            
        print("Đã dọn dẹp xong tài nguyên mạng")
    
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
        self.is_discovering = False

    def start_heartbeat_service(self):
        """Khởi động service gửi và nhận heartbeat"""
        threading.Thread(target=self.send_heartbeat, daemon=True).start()
        threading.Thread(target=self.check_nodes_status, daemon=True).start()

    def send_heartbeat(self):
        """Gửi tín hiệu heartbeat định kỳ"""
        while self.is_listening:
            heartbeat_message = {
                "type": "heartbeat",
                "node_id": self.node_id,
                "timestamp": time.time()
            }
            self.broadcast_message(heartbeat_message)
            time.sleep(self.heartbeat_interval)

    def check_nodes_status(self):
        """Kiểm tra trạng thái các node dựa trên heartbeat"""
        while self.is_listening:
            current_time = time.time()
            offline_nodes = []

            with self._lock:
                for node in list(self.nodes):
                    last_seen = self.node_last_seen.get(node, 0)
                    if current_time - last_seen > self.offline_threshold:
                        offline_nodes.append(node)
                        self.nodes.remove(node)
                        if node in self.active_connections:
                            self.active_connections[node].close()
                            del self.active_connections[node]

            # Thông báo các node offline
            for node in offline_nodes:
                self.notify('node_offline', {'node_id': node})
                self.broadcast_node_status(node, "offline")

            time.sleep(30)  # Kiểm tra mỗi 30 giây

    def handle_heartbeat(self, message):
        """Xử lý tin nhắn heartbeat từ node khác"""
        node_id = message.get("node_id")
        timestamp = message.get("timestamp")
        
        with self._lock:
            # Cập nhật thời gian cuối cùng thấy node
            self.node_last_seen[node_id] = timestamp
            
            # Nếu node này trước đó offline, đánh dấu là online
            if node_id not in self.nodes:
                self.nodes.add(node_id)
                self.notify('node_online', {'node_id': node_id})
                self.broadcast_node_status(node_id, "online")

    def broadcast_node_status(self, node_id, status):
        """Gửi thông báo về trạng thái của node cho tất cả các node khác"""
        status_message = {
            "type": "node_status",
            "node_id": node_id,
            "status": status,
            "timestamp": time.time()
        }
        self.broadcast_message(status_message)


