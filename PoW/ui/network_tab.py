
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import time

class NetworkTab:
    def __init__(self, parent, network):
        self.parent = parent
        self.network = network
        
        self.frame = ttk.Frame(parent)
        self.scanning = False
        self.node_status = {}  # Dictionary to track node status
        
        # Đăng ký các callbacks
        self.network.add_callback('new_transaction', self.on_new_transaction)
        self.network.add_callback('new_block', self.on_new_block)
        self.network.add_callback('new_node', self.on_new_node)
        self.network.add_callback('chain_updated', self.on_chain_updated)
        
        # Đăng ký các callback mới
        self.network.callbacks['sync_started'].append(self.on_sync_started)
        self.network.callbacks['sync_completed'].append(self.on_sync_completed)
        self.network.callbacks['sync_failed'].append(self.on_sync_failed)
        
        # Thêm frame thông báo
        self.notification_frame = ttk.LabelFrame(self.frame, text="Thông báo mạng")
        self.notification_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.notification_label = ttk.Label(self.notification_frame, text="")
        self.notification_label.pack(pady=5)
        
        # Thêm label thông báo đồng bộ
        self.sync_status_label = ttk.Label(self.frame, text="")
        self.sync_status_label.pack(pady=5)
        
        # Thêm progress bar
        self.sync_progress = ttk.Progressbar(
            self.frame,
            orient="horizontal",
            length=300,
            mode="determinate"
        )
        self.sync_progress.pack(pady=5)
        self.sync_progress.pack_forget()  # Ẩn ban đầu
        
        # Thêm callbacks cho trạng thái node
        self.network.add_callback('node_offline', self.on_node_offline)
        self.network.add_callback('node_online', self.on_node_online)
        
        # Bắt đầu thread kiểm tra trạng thái node
        self.node_check_thread = threading.Thread(target=self.check_nodes_status, daemon=True)
        self.node_check_thread.start()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các widget cho tab mạng"""
        # Frame thông tin mạng
        info_frame = ttk.LabelFrame(self.frame, text="Thông tin mạng")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Địa chỉ IP
        ttk.Label(info_frame, text="Địa chỉ IP:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.ip_label = ttk.Label(info_frame, text=self.network.get_local_ip())
        self.ip_label.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Cổng
        ttk.Label(info_frame, text="Cổng:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.port_label = ttk.Label(info_frame, text=str(self.network.port))
        self.port_label.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Số node đã kết nối
        ttk.Label(info_frame, text="Số node đã kết nối:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.nodes_count_label = ttk.Label(info_frame, text="0")
        self.nodes_count_label.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Nút làm mới
        ttk.Button(info_frame, text="Làm mới", command=self.update_network_info).grid(
            row=3, column=0, columnspan=2, padx=10, pady=5)
        
        # Frame kết nối
        connect_frame = ttk.LabelFrame(self.frame, text="Kết nối với node")
        connect_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Địa chỉ IP
        ttk.Label(connect_frame, text="Địa chỉ IP:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.connect_ip_entry = ttk.Entry(connect_frame, width=15)
        self.connect_ip_entry.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Cổng
        ttk.Label(connect_frame, text="Cổng:").grid(row=0, column=2, padx=10, pady=5, sticky=tk.W)
        self.connect_port_entry = ttk.Entry(connect_frame, width=6)
        self.connect_port_entry.grid(row=0, column=3, padx=10, pady=5, sticky=tk.W)
        self.connect_port_entry.insert(0, "5000")
        
        # Nút kết nối
        ttk.Button(connect_frame, text="Kết nối", command=self.connect_to_node).grid(
            row=0, column=4, padx=10, pady=5)
        
        # Nút quét mạng LAN
        self.scan_button = ttk.Button(connect_frame, text="Quét mạng LAN", command=self.toggle_scan)
        self.scan_button.grid(row=1, column=0, columnspan=5, padx=10, pady=5)
        
        # Thêm progress bar cho quá trình quét
        self.scan_progress = ttk.Progressbar(
            connect_frame, 
            mode='indeterminate'
        )
        self.scan_progress.grid(row=2, column=0, columnspan=5, padx=10, pady=5)
        self.scan_progress.grid_remove()  # Ẩn ban đầu
        
        # Frame danh sách node
        nodes_frame = ttk.LabelFrame(self.frame, text="Danh sách node đã kết nối")
        nodes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview để hiển thị danh sách node
        columns = ("address", "port", "status", "last_seen")
        self.nodes_tree = ttk.Treeview(nodes_frame, columns=columns, show="headings")
        
        # Định nghĩa các cột
        self.nodes_tree.heading("address", text="Địa chỉ IP")
        self.nodes_tree.heading("port", text="Cổng")
        self.nodes_tree.heading("status", text="Trạng thái")
        self.nodes_tree.heading("last_seen", text="Lần cuối online")
        
        # Thiết lập độ rộng cột
        self.nodes_tree.column("address", width=200)
        self.nodes_tree.column("port", width=100)
        self.nodes_tree.column("status", width=150)
        self.nodes_tree.column("last_seen", width=150)
        
        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(nodes_frame, orient=tk.VERTICAL, command=self.nodes_tree.yview)
        self.nodes_tree.configure(yscroll=scrollbar.set)
        
        # Pack các widget
        self.nodes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Thêm menu chuột phải
        self.context_menu = tk.Menu(self.nodes_tree, tearoff=0)
        self.context_menu.add_command(label="Ngắt kết nối", command=self.disconnect_node)
        self.context_menu.add_command(label="Kiểm tra kết nối", command=self.check_selected_node)
        
        self.nodes_tree.bind("<Button-3>", self.show_context_menu)
        
        # Cập nhật thông tin mạng
        self.update_network_info()
        
        # Lập lịch cập nhật định kỳ
        self.schedule_update()
    
    def update_network_info(self):
        """Cập nhật thông tin mạng"""
        # Cập nhật địa chỉ IP
        self.ip_label.config(text=self.network.get_local_ip())
        
        # Cập nhật cổng
        self.port_label.config(text=str(self.network.port))
        
        # Cập nhật số node đã kết nối
        active_nodes = sum(1 for status in self.node_status.values() if status == "Đã kết nối")
        self.nodes_count_label.config(text=str(active_nodes))
        
        # Cập nhật danh sách node
        self.update_nodes_list()
    
    def update_nodes_list(self):
        """Cập nhật danh sách node"""
        # Lưu trữ các node hiện tại trong tree
        current_nodes = set()
        for item in self.nodes_tree.get_children():
            values = self.nodes_tree.item(item, "values")
            if values:
                node_id = f"{values[0]}:{values[1]}"
                current_nodes.add(node_id)
        
        # Cập nhật node_status với các node mới
        for node in self.network.nodes:
            if node not in self.node_status:
                self.node_status[node] = "Đang kiểm tra..."
        
        # Xóa các node không còn trong danh sách network.nodes
        nodes_to_remove = []
        for node in self.node_status:
            if node not in self.network.nodes and self.node_status[node] != "Không phản hồi":
                nodes_to_remove.append(node)
        
        for node in nodes_to_remove:
            del self.node_status[node]
        
        # Cập nhật hoặc thêm mới các node vào treeview
        for node in self.node_status:
            try:
                address, port = node.split(":")
                status = self.node_status[node]
                
                # Tìm node trong treeview
                node_item = None
                for item in self.nodes_tree.get_children():
                    values = self.nodes_tree.item(item, "values")
                    if values and f"{values[0]}:{values[1]}" == node:
                        node_item = item
                        break
                
                # Cập nhật hoặc thêm mới
                if node_item:
                    self.nodes_tree.item(node_item, values=(address, port, status, time.strftime('%H:%M:%S', time.localtime())))
                    if status == "Đã kết nối":
                        self.nodes_tree.item(node_item, tags=("connected",))
                    elif status == "Không phản hồi":
                        self.nodes_tree.item(node_item, tags=("disconnected",))
                    else:
                        self.nodes_tree.item(node_item, tags=("checking",))
                else:
                    item_id = self.nodes_tree.insert("", tk.END, values=(address, port, status, time.strftime('%H:%M:%S', time.localtime())))
                    if status == "Đã kết nối":
                        self.nodes_tree.item(item_id, tags=("connected",))
                    elif status == "Không phản hồi":
                        self.nodes_tree.item(item_id, tags=("disconnected",))
                    else:
                        self.nodes_tree.item(item_id, tags=("checking",))
            except:
                continue
        
        # Xóa các node không còn trong node_status
        for item in self.nodes_tree.get_children():
            values = self.nodes_tree.item(item, "values")
            if values:
                node_id = f"{values[0]}:{values[1]}"
                if node_id not in self.node_status:
                    self.nodes_tree.delete(item)
        
        # Cấu hình màu sắc cho các trạng thái
        self.nodes_tree.tag_configure("connected", foreground="green")
        self.nodes_tree.tag_configure("disconnected", foreground="red")
        self.nodes_tree.tag_configure("checking", foreground="blue")
    
    def check_nodes_status(self):
        """Kiểm tra trạng thái của tất cả các node trong một thread riêng"""
        while True:
            for node in list(self.network.nodes):
                try:
                    address, port = node.split(":")
                    port = int(port)
                    
                    # Tạo socket và thử kết nối
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)  # Timeout 2 giây
                    result = s.connect_ex((address, port))
                    s.close()
                    
                    if result == 0:
                        self.node_status[node] = "Đã kết nối"
                    else:
                        self.node_status[node] = "Không phản hồi"
                        # Nếu node không phản hồi, xóa khỏi danh sách nodes
                        if node in self.network.nodes:
                            self.network.nodes.remove(node)
                except:
                    if node in self.node_status:
                        self.node_status[node] = "Không phản hồi"
                    if node in self.network.nodes:
                        self.network.nodes.remove(node)
            
            # Cập nhật UI từ thread chính
            if hasattr(self, 'parent'):
                self.parent.after(0, self.update_network_info)
            
            # Kiểm tra mỗi 30 giây
            time.sleep(30)
    
    def check_selected_node(self):
        """Kiểm tra kết nối với node đã chọn"""
        selected = self.nodes_tree.selection()
        if not selected:
            return
        
        item = selected[0]
        node_info = self.nodes_tree.item(item, "values")
        if not node_info:
            return
        
        address, port = node_info[0], node_info[1]
        node = f"{address}:{port}"
        
        # Cập nhật trạng thái
        self.nodes_tree.item(item, values=(address, port, "Đang kiểm tra..."))
        self.nodes_tree.item(item, tags=("checking",))
        
        # Kiểm tra kết nối trong thread riêng
        def check_connection():
            try:
                port_int = int(port)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                result = s.connect_ex((address, port_int))
                s.close()
                
                if result == 0:
                    status = "Đã kết nối"
                    tag = "connected"
                    if node not in self.network.nodes:
                        self.network.nodes.append(node)
                else:
                    status = "Không phản hồi"
                    tag = "disconnected"
                    if node in self.network.nodes:
                        self.network.nodes.remove(node)
                
                self.node_status[node] = status
                
                # Cập nhật UI từ thread chính
                self.parent.after(0, lambda: self.update_node_status(item, address, port, status, tag))
            except Exception as e:
                status = "Lỗi: " + str(e)
                self.parent.after(0, lambda: self.update_node_status(item, address, port, status, "disconnected"))
        
        threading.Thread(target=check_connection, daemon=True).start()
    
    def update_node_status(self, item, address, port, status, tag):
        """Cập nhật trạng thái node trong UI"""
        self.nodes_tree.item(item, values=(address, port, status))
        self.nodes_tree.item(item, tags=(tag,))
        self.update_network_info()
    
    def connect_to_node(self):
        """Kết nối đến một node"""
        # Lấy thông tin kết nối
        ip = self.connect_ip_entry.get().strip()
        port_str = self.connect_port_entry.get().strip()
        
        # Kiểm tra dữ liệu đầu vào
        if not ip:
            messagebox.showerror("Lỗi", "Vui lòng nhập địa chỉ IP")
            return
        
        try:
            port = int(port_str)
            if port < 1024 or port > 65535:
                raise ValueError("Cổng phải nằm trong khoảng 1024-65535")
        except ValueError:
            messagebox.showerror("Lỗi", "Cổng không hợp lệ")
            return
        
        # Kết nối đến node
        def connect():
            node = f"{ip}:{port}"
            self.node_status[node] = "Đang kết nối..."
            self.update_network_info()
            
            if self.network.connect_to_node(ip, port):
                self.node_status[node] = "Đã kết nối"
                messagebox.showinfo("Thành công", f"Đã kết nối đến {ip}:{port}")
            else:
                self.node_status[node] = "Không phản hồi"
                messagebox.showerror("Lỗi", f"Không thể kết nối đến {ip}:{port}")
            
            self.update_network_info()
        
        # Tạo thread để kết nối
        threading.Thread(target=connect, daemon=True).start()
    
    def toggle_scan(self):
        """Bắt đầu hoặc dừng quét mạng LAN"""
        if self.scanning:
            self.scanning = False
            self.network.is_discovering = False
            self.scan_button.config(text="Quét mạng LAN")
            self.scan_progress.grid_remove()
        else:
            self.scanning = True
            self.scan_button.config(text="Dừng quét")
            self.scan_progress.grid()
            self.scan_progress.start()
            
            # Bắt đầu quét
            self.network.discover_nodes()
    
    def scan_network(self):
        """Quét mạng LAN để tìm các node"""
        while self.scanning:
            self.network.discover_nodes()
            self.update_network_info()
            time.sleep(5)  # Quét mỗi 5 giây
    
    def show_context_menu(self, event):
        """Hiển thị menu chuột phải"""
        item = self.nodes_tree.identify_row(event.y)
        if item:
            self.nodes_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def disconnect_node(self):
        """Ngắt kết nối với node đã chọn"""
        selected = self.nodes_tree.selection()
        if not selected:
            return
        
        item = selected[0]
        node_info = self.nodes_tree.item(item, "values")
        if not node_info:
            return
        
        address, port = node_info[0], node_info[1]
        node = f"{address}:{port}"
        
        # Xóa node khỏi danh sách
        if node in self.network.nodes:
            self.network.nodes.remove(node)
            self.node_status[node] = "Không phản hồi"
            messagebox.showinfo("Thành công", f"Đã ngắt kết nối với {node}")
            self.update_network_info()
    
    def schedule_update(self):
        """Lập lịch cập nhật định kỳ"""
        self.update_network_info()
        self.parent.after(10000, self.schedule_update)  # Cập nhật mỗi 10 giây

    def show_notification(self, message, duration=3000):
        """Hiển thị thông báo và tự động ẩn sau duration ms"""
        self.notification_label.config(text=message)
        self.frame.after(duration, lambda: self.notification_label.config(text=""))

    def on_new_transaction(self, data):
        tx = data['transaction']
        self.show_notification(
            f"Nhận giao dịch mới từ {tx['sender']} đến {tx['receiver']} "
            f"(từ node {data['from_node']})"
        )
        self.update_network_info()

    def on_new_block(self, data):
        block = data['block']
        self.show_notification(
            f"Nhận block mới #{block.index} từ node {data['from_node']}"
        )
        self.update_network_info()

    def on_new_node(self, data):
        node_id = data['node_id']
        self.show_notification(
            f"Node mới tham gia mạng: {node_id}"
        )
        # Thêm node mới vào danh sách theo dõi trạng thái
        if node_id not in self.node_status:
            self.node_status[node_id] = "Đã kết nối"
        self.update_network_info()

    def on_chain_updated(self, data):
        self.show_notification(
            f"Cập nhật blockchain từ {data['old_length']} lên {data['new_length']} blocks"
        )
        self.update_network_info()

    def on_sync_started(self, data):
        """Xử lý khi bắt đầu đồng bộ"""
        current_length = data['current_length']
        target_length = data['target_length']
        blocks_to_sync = target_length - current_length
        
        self.sync_status_label.config(
            text=f"Đang đồng bộ... ({current_length} → {target_length} blocks)",
            foreground="blue"
        )
        
        # Hiển thị và cập nhật progress bar
        self.sync_progress.pack()
        self.sync_progress["maximum"] = blocks_to_sync
        self.sync_progress["value"] = 0
        
        # Cập nhật giao diện
        self.parent.update()

    def on_sync_completed(self, data):
        """Xử lý khi đồng bộ hoàn tất"""
        new_length = data['new_length']
        blocks_synced = data['blocks_synced']
        
        self.sync_status_label.config(
            text=f"Đã đồng bộ thành công {blocks_synced} blocks. Tổng số blocks: {new_length}",
            foreground="green"
        )
        
        # Ẩn progress bar sau 3 giây
        self.parent.after(3000, self.sync_progress.pack_forget)
        
        # Xóa thông báo sau 5 giây
        self.parent.after(5000, lambda: self.sync_status_label.config(text=""))

    def on_sync_failed(self, data):
        """Xử lý khi đồng bộ thất bại"""
        reason = data['reason']
        current_length = data['current_length']
        
        self.sync_status_label.config(
            text=f"Đồng bộ thất bại: {reason}. Blocks hiện tại: {current_length}",
            foreground="red"
        )
        
        # Ẩn progress bar
        self.sync_progress.pack_forget()
        
        # Xóa thông báo sau 5 giây
        self.parent.after(5000, lambda: self.sync_status_label.config(text=""))

    def on_node_offline(self, data):
        """Xử lý khi node offline"""
        node_id = data['node_id']
        self.update_node_status_ui(node_id, "Offline", "red")
        self.show_notification(f"Node {node_id} đã offline")

    def on_node_online(self, data):
        """Xử lý khi node online"""
        node_id = data['node_id']
        self.update_node_status_ui(node_id, "Online", "green")
        self.show_notification(f"Node {node_id} đã online")

    def update_node_status_ui(self, node_id, status, color):
        """Cập nhật trạng thái node trong UI"""
        for item in self.nodes_tree.get_children():
            values = self.nodes_tree.item(item)['values']
            if f"{values[0]}:{values[1]}" == node_id:
                self.nodes_tree.item(
                    item,
                    values=(values[0], values[1], status, 
                           time.strftime('%H:%M:%S', time.localtime())),
                    tags=(color,)
                )
                break

