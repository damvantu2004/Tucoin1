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
        
        # Frame danh sách node
        nodes_frame = ttk.LabelFrame(self.frame, text="Danh sách node đã kết nối")
        nodes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview để hiển thị danh sách node
        columns = ("address", "port", "status")
        self.nodes_tree = ttk.Treeview(nodes_frame, columns=columns, show="headings")
        
        # Định nghĩa các cột
        self.nodes_tree.heading("address", text="Địa chỉ IP")
        self.nodes_tree.heading("port", text="Cổng")
        self.nodes_tree.heading("status", text="Trạng thái")
        
        # Thiết lập độ rộng cột
        self.nodes_tree.column("address", width=200)
        self.nodes_tree.column("port", width=100)
        self.nodes_tree.column("status", width=150)
        
        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(nodes_frame, orient=tk.VERTICAL, command=self.nodes_tree.yview)
        self.nodes_tree.configure(yscroll=scrollbar.set)
        
        # Pack các widget
        self.nodes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Thêm menu chuột phải
        self.context_menu = tk.Menu(self.nodes_tree, tearoff=0)
        self.context_menu.add_command(label="Ngắt kết nối", command=self.disconnect_node)
        
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
        self.nodes_count_label.config(text=str(len(self.network.nodes)))
        
        # Cập nhật danh sách node
        self.update_nodes_list()
    
    def update_nodes_list(self):
        """Cập nhật danh sách node"""
        # Xóa dữ liệu cũ
        for item in self.nodes_tree.get_children():
            self.nodes_tree.delete(item)
        
        # Thêm các node đã kết nối
        for node in self.network.nodes:
            try:
                address, port = node.split(":")
                
                # Kiểm tra kết nối
                status = "Đã kết nối"
                
                # Thêm vào treeview
                self.nodes_tree.insert("", tk.END, values=(address, port, status), tags=(node,))
            except:
                continue
    
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
                raise ValueError("Cổng phải n���m trong khoảng 1024-65535")
        except ValueError:
            messagebox.showerror("Lỗi", "Cổng không hợp lệ")
            return
        
        # Kết nối đến node
        def connect():
            if self.network.connect_to_node(ip, port):
                messagebox.showinfo("Thành công", f"Đã kết nối đến {ip}:{port}")
                self.update_network_info()
            else:
                messagebox.showerror("Lỗi", f"Không thể kết nối đến {ip}:{port}")
        
        # Tạo thread để kết nối
        threading.Thread(target=connect, daemon=True).start()
    
    def toggle_scan(self):
        """Bắt đầu hoặc dừng quét mạng LAN"""
        if self.scanning:
            self.scanning = False
            self.scan_button.config(text="Quét mạng LAN")
        else:
            self.scanning = True
            self.scan_button.config(text="Dừng quét")
            
            # Tạo thread để quét mạng
            threading.Thread(target=self.scan_network, daemon=True).start()
    
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
            messagebox.showinfo("Thành công", f"Đã ngắt kết nối với {node}")
            self.update_network_info()
    
    def schedule_update(self):
        """Lập lịch cập nhật định kỳ"""
        self.update_network_info()
        self.parent.after(10000, self.schedule_update)  # Cập nhật mỗi 10 giây