# KIẾN TRÚC ỨNG DỤNG TUCOIN
## Mục lục
1. Tổng quan
2. Mô hình MVC
3. Cấu trúc thư mục
4. Luồng hoạt động
5. Ưu điểm & Thách thức
6. Demo thực tế

## 1. Tổng quan
### 1.1. Giới thiệu
TuCoin là ứng dụng blockchain với giao diện đồ họa (GUI) cho phép:
- Đào coin
- Tạo và quản lý ví
- Thực hiện giao dịch
- Xem lịch sử blockchain

### 1.2. Công nghệ sử dụng
- Python 3.6+
- Tkinter (GUI)
- JSON (lưu trữ)
- hashlib (mã hóa)
- threading (xử lý đa luồng)

## 2. Mô hình MVC
### 2.1. Model (src/)
Xử lý business logic và data:

#### 2.1.1. Blockchain (blockchain.py)
```python
class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        
    def mine_block(self, miner_address):
        # Logic đào block
```

#### 2.1.2. Wallet (wallet.py)
```python
class Wallet:
    def __init__(self, blockchain):
        self.addresses = []
        self.current_address = None
        
    def get_balance(self, address):
        # Logic tính số dư
```

### 2.2. View (ui/)
Giao diện người dùng:

#### 2.2.1. MainWindow (main_window.py)
```python
class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.notebook = ttk.Notebook()
        # Tạo các tab
```

#### 2.2.2. MiningTab (mining_tab.py)
```python
class MiningTab:
    def __init__(self):
        self.mining_button = ttk.Button()
        self.log_text = tk.Text()
```

### 2.3. Controller
Xử lý tương tác:

#### 2.3.1. Mining Controller
```python
def start_mining(self):
    """Controller cho mining"""
    address = self.get_wallet_address()
    if self.validate_address(address):
        self.blockchain.mine_block(address)
        self.update_ui()
```

#### 2.3.2. Wallet Controller
```python
def send_transaction(self):
    """Controller cho giao dịch"""
    if self.validate_transaction():
        self.wallet.create_transaction()
        self.update_balance()
```

## 3. Cấu trúc thư mục
```
tucoin-app/
├── src/                    # Models
│   ├── blockchain.py
│   ├── wallet.py
│   └── transaction.py
├── ui/                     # Views
│   ├── main_window.py
│   ├── mining_tab.py
│   └── wallet_tab.py
└── data/                   # Storage
    ├── blockchain.json
    └── wallet.json
```

## 4. Luồng hoạt động
### 4.1. Luồng đào coin
1. User click "Bắt đầu đào" (View)
2. Controller kiểm tra địa chỉ ví
3. Model thực hiện đào block
4. Controller cập nhật UI
5. View hiển thị kết quả

### 4.2. Luồng giao dịch
1. User nhập thông tin giao dịch (View)
2. Controller validate input
3. Model tạo và xử lý giao dịch
4. Controller cập nhật số dư
5. View hiển thị trạng thái

## 5. Ưu điểm & Thách thức
### 5.1. Ưu điểm
- **Tách biệt**: Logic và UI độc lập
- **Bảo trì**: Dễ sửa đổi từng phần
- **Mở rộng**: Thêm tính năng không ảnh hưởng cấu trúc
- **Tái sử dụng**: Model dùng cho nhiều View

### 5.2. Thách thức
- Đồng bộ hóa Model và View
- Xử lý đa luồng trong GUI
- Quản lý trạng thái phức tạp
- Scale khi thêm tính năng

## 6. Demo thực tế
### 6.1. Mining Feature
```python
# View (mining_tab.py)
mining_button.click()

# Controller
def start_mining():
    address = wallet.get_current_address()
    blockchain.mine_block(address)
    update_ui()

# Model (blockchain.py)
def mine_block(address):
    # Create new block
    # Add mining reward
    # Update chain
```

### 6.2. Transaction Feature
```python
# View (wallet_tab.py)
send_button.click()

# Controller
def send_transaction():
    if validate_input():
        wallet.create_transaction()
        update_balance()

# Model (wallet.py)
def create_transaction():
    # Verify balance
    # Create transaction
    # Add to pending
```

## 7. Kết luận
TuCoin sử dụng MVC để:
- Tách biệt logic và giao diện
- Dễ dàng mở rộng và bảo trì
- Quản lý code hiệu quả
- Tối ưu trải nghiệm người dùng

## 8. Hướng phát triển
- Tách Controller thành module riêng
- Thêm Observer pattern
- Cải thiện xử lý đa luồng
- Tối ưu hiệu năng