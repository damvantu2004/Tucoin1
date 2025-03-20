# TuCoin Blockchain App - Đơn giản & Trực quan

## Giới thiệu
TuCoin là ứng dụng blockchain đơn giản với giao diện đồ họa (GUI) thân thiện, cho phép người dùng đào coin và kết nối với nhau trong mạng ngang hàng (P2P).

![TuCoin GUI Preview](https://via.placeholder.com/800x500?text=TuCoin+GUI+Preview)

## Tính năng chính
- **Giao diện đồ họa trực quan** - Dễ sử dụng, không cần kiến thức chuyên sâu
- **Đào coin đơn giản** - Nhận 100 TuCoin cho mỗi khối đào được
- **Kết nối P2P** - Tự động tìm và kết nối với các node khác trong mạng LAN
- **Giao dịch nhanh chóng** - Gửi và nhận TuCoin giữa các người dùng
- **Xem số dư và lịch sử** - Theo dõi số coin và các giao dịch của bạn
- **Cơ chế đồng thuận linh hoạt** - Dễ dàng chuyển đổi giữa Proof of Work (PoW) và Proof of Stake (PoS)

## Cấu trúc dự án
```
tucoin-app/
│
├── README.md                # Tài liệu dự án
├── requirements.txt         # Thư viện cần thiết
├── tucoin.py                # File chính của ứng dụng
│
├── src/                     # Mã nguồn
│   ├── blockchain.py        # Lớp Blockchain, Block cơ bản
│   ├── transaction.py       # Lớp Transaction
│   ├── consensus/           # Module đồng thuận
│   │   ├── __init__.py
│   │   ├── base.py          # Interface chung cho cơ chế đồng thuận
│   │   ├── pow.py           # Triển khai Proof of Work
│   │   └── pos.py           # Triển khai Proof of Stake
│   ├── network.py           # Kết nối P2P
│   └── wallet.py            # Quản lý ví và giao dịch
│
├── ui/                      # Giao diện người dùng
│   ├── main_window.py       # Cửa sổ chính
│   ├── mining_tab.py        # Tab đào coin
│   ├── wallet_tab.py        # Tab ví điện tử
│   └── network_tab.py       # Tab kết nối mạng
│
└── data/                    # Dữ liệu
    ├── blockchain.json      # Lưu trữ blockchain
    └── wallet.json          # Lưu trữ ví và giao dịch
```

## Yêu cầu hệ thống
- Python 3.6+
- Tkinter (GUI)
- Socket (kết nối mạng)
- hashlib, json (xử lý blockchain)

## Cài đặt và chạy
1. Clone repository:
   ```
   git clone https://github.com/yourusername/tucoin-app.git
   cd tucoin-app
   ```

2. Cài đặt các thư viện cần thiết:
   ```
   pip install -r requirements.txt
   ```

3. Chạy ứng dụng:
   ```
   python tucoin.py
   ```

## Hướng dẫn sử dụng

### Đào coin
1. Mở tab "Đào Coin"
2. Nhập địa chỉ ví của bạn (hoặc sử dụng địa chỉ mặc định)
3. Chọn cơ chế đồng thuận (PoW hoặc PoS) từ menu thả xuống
4. Nhấn nút "Bắt đầu đào" để bắt đầu quá trình đào
5. Mỗi khối đào thành công sẽ nhận được 100 TuCoin

### Kết nối với người dùng khác
1. Mở tab "Mạng"
2. Ứng dụng sẽ tự động tìm kiếm các node trong mạng LAN
3. Hoặc nhập địa chỉ IP của node khác để kết nối thủ công
4. Danh sách các node đã kết nối sẽ hiển thị trong tab

### Gửi/Nhận coin
1. Mở tab "Ví"
2. Xem số dư hiện tại của bạn
3. Để gửi coin, nhập địa chỉ người nhận và số lượng
4. Nhấn "Gửi" để hoàn tất giao dịch

### Chuyển đổi cơ chế đồng thuận
1. Mở tab "Cài đặt"
2. Chọn cơ chế đồng thuận mong muốn (PoW hoặc PoS)
3. Điều chỉnh các tham số cho cơ chế đã chọn (độ khó cho PoW, số coin tối thiểu cho PoS)
4. Lưu cài đặt và khởi động lại mạng

## Mô hình dữ liệu đơn giản

### Block
- **index**: Số thứ tự của khối
- **timestamp**: Thời gian tạo khối
- **transactions**: Danh sách giao dịch
- **consensus_data**: Dữ liệu đồng thuận (nonce cho PoW, validator cho PoS)
- **previous_hash**: Hash của khối trước
- **hash**: Hash của khối hiện tại

### Transaction
- **sender**: Địa chỉ người gửi
- **receiver**: Địa chỉ người nhận
- **amount**: Số lượng TuCoin
- **timestamp**: Thời gian giao dịch

## Cơ chế đồng thuận
Ứng dụng hỗ trợ hai cơ chế đồng thuận:

### Proof of Work (PoW)
- Tìm giá trị nonce sao cho hash của khối bắt đầu bằng một số lượng số 0 nhất định
- Độ khó có thể điều chỉnh để phù hợp với hiệu suất máy tính
- Tiêu tốn nhiều tài nguyên tính toán

### Proof of Stake (PoS)
- Người dùng có thể đặt cọc (stake) TuCoin để có cơ hội tạo khối mới
- Cơ hội được chọn tỷ lệ thuận với số lượng coin đặt cọc
- Tiết kiệm năng lượng hơn so với PoW
- Yêu cầu số dư tối thiểu để tham gia

### Chuyển đổi giữa các cơ chế
- Thiết kế module hóa cho phép chuyển đổi dễ dàng giữa các cơ chế
- Giao diện chung (interface) đảm bảo tính nhất quán
- Cài đặt mới được áp dụng cho các khối mới, không ảnh hưởng đến chuỗi hiện có

## Phát triển trong tương lai
- Cải thiện cơ chế Proof of Stake
- Thêm cơ chế đồng thuận mới (DPoS, PBFT)
- Cải thiện bảo mật với chữ ký số
- Tối ưu hóa hiệu suất mạng
- Thêm tính năng sao lưu và khôi phục ví
- Giao diện web cho phép truy cập từ xa

## Đóng góp
Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request.

## Giấy phép
MIT License
