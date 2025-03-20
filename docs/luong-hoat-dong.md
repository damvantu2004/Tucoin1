# LUỒNG HOẠT ĐỘNG CỦA ỨNG DỤNG TUCOIN
1.Tổng quan hệ thống - giới thiệu về các chức năng chính của ứng dụng
2.Quy trình khởi động - các bước từ khi ứng dụng được chạy
3.Cấu trúc ứng dụng - phân tích chi tiết các thành phần cốt lõi và giao diện người dùng
4.Luồng hoạt động chính - quy trình xử lý chính của ứng dụng
5.Luồng dữ liệu giữa các thành phần - cách các module tương tác với nhau
6.Các cơ chế xử lý đồng thời - các thread chạy song song trong ứng dụng
7.Lưu trữ dữ liệu - cách ứng dụng lưu trữ và quản lý dữ liệu
## 1. Tổng quan hệ thống

TuCoin là một ứng dụng blockchain đơn giản được xây dựng trên nền tảng Python với giao diện đồ họa sử dụng Tkinter. Ứng dụng có các chức năng cơ bản của một cryptocurrency bao gồm:

- Quản lý ví (tạo ví, xem số dư, gửi coin)
- Đào coin (sử dụng 2 cơ chế Proof of Work và Proof of Stake)
- Kết nối mạng (kết nối P2P giữa các node)
- Quản lý blockchain (tạo block, xác thực giao dịch)

## 2. Khởi động ứng dụng

Khi ứng dụng được khởi động, file `tucoin.py` là điểm vào chính và thực hiện các bước sau:

1. **Xử lý tham số dòng lệnh**: Cho phép người dùng chỉ định cổng lắng nghe (mặc định 5000) và địa chỉ node để kết nối.
2. **Tạo thư mục dữ liệu**: Tạo thư mục `data` nếu chưa tồn tại.
3. **Khởi tạo blockchain**: Tạo đối tượng blockchain mới hoặc tải từ file nếu đã tồn tại.
4. **Khởi tạo ví**: Tạo ví mới hoặc tải từ file nếu đã tồn tại.
5. **Khởi tạo mạng**: Thiết lập kết nối mạng với cổng đã chỉ định.
6. **Kết nối với node khác**: Kết nối đến node đã được chỉ định khi khởi động (nếu có).
7. **Tạo thread tự động lưu**: Lưu blockchain và ví theo định kỳ (mỗi 60 giây).
8. **Khởi động giao diện người dùng**: Hiển thị giao diện chính của ứng dụng.

## 3. Cấu trúc ứng dụng

### 3.1. Core Components

#### 3.1.1. Blockchain (`src/blockchain.py`)

Blockchain là thành phần trung tâm của ứng dụng, chịu trách nhiệm:
- Lưu trữ các khối (blocks) trong chuỗi
- Quản lý các giao dịch đang chờ (pending transactions)
- Xác thực tính toàn vẹn của chuỗi
- Đào các khối mới

**Luồng hoạt động của Blockchain**:
1. **Khởi tạo**: Tạo khối genesis (khối đầu tiên)
2. **Thêm giao dịch**: Giao dịch được thêm vào danh sách chờ (pending)
3. **Đào khối mới**: Tìm giá trị proof hợp lệ và tạo khối mới
4. **Xác thực khối**: Kiểm tra tính hợp lệ của các khối
5. **Lưu/Tải blockchain**: Lưu trữ và khôi phục blockchain từ file JSON

#### 3.1.2. Ví (`src/wallet.py`)

Wallet (Ví) quản lý:
- Các địa chỉ của người dùng
- Khóa riêng tư (private keys)
- Số dư coin
- Giao dịch gửi và nhận

**Luồng hoạt động của Wallet**:
1. **Tạo địa chỉ mới**: Tạo một private key và địa chỉ tương ứng
2. **Tính toán số dư**: Duyệt qua tất cả các giao dịch trong blockchain để tính số dư
3. **Gửi coin**: Tạo giao dịch mới và thêm vào blockchain
4. **Lấy lịch sử giao dịch**: Duyệt qua blockchain để lấy giao dịch liên quan đến địa chỉ
5. **Lưu/Tải ví**: Lưu trữ và khôi phục thông tin ví từ file JSON

#### 3.1.3. Mạng (`src/network.py`)

Network quản lý kết nối P2P giữa các node, bao gồm:
- Khởi động server để lắng nghe kết nối
- Kết nối đến các node khác
- Đồng bộ hóa blockchain giữa các node
- Broadcast các khối và giao dịch mới

**Luồng hoạt động của Network**:
1. **Khởi động server**: Lắng nghe kết nối từ các node khác
2. **Kết nối đến node**: Thiết lập kết nối TCP đến node khác
3. **Xử lý message**: Nhận và xử lý các loại message (get_chain, chain, new_block, new_transaction)
4. **Broadcast**: Gửi thông tin khối mới/giao dịch mới đến tất cả các node đã kết nối
5. **Kiểm tra chain**: So sánh và cập nhật blockchain nếu nhận được chain dài hơn và hợp lệ

#### 3.1.4. Cơ chế đồng thuận (`src/consensus/`)

Hệ thống hỗ trợ hai cơ chế đồng thuận:
- **Proof of Work (PoW)**: Dựa trên sức mạnh tính toán
- **Proof of Stake (PoS)**: Dựa trên số lượng coin đã stake

**Luồng hoạt động của Consensus**:
1. **PoW**: 
   - Tìm giá trị nonce để hash của khối bắt đầu bằng n số 0
   - Khối được tạo khi tìm thấy nonce hợp lệ
   - Phần thưởng: 100 TuCoin

2. **PoS**:
   - Người dùng stake một số lượng coin nhất định
   - Validator được chọn ngẫu nhiên dựa trên số lượng coin đã stake
   - Phần thưởng: 10 TuCoin (ít hơn PoW)

### 3.2. Giao diện người dùng

Giao diện người dùng được xây dựng bằng Tkinter, gồm 3 tab chính:

#### 3.2.1. Tab Ví (`ui/wallet_tab.py`)

- Hiển thị thông tin ví (địa chỉ, số dư)
- Cho phép tạo ví mới
- Cho phép gửi coin đến địa chỉ khác
- Hiển thị lịch sử giao dịch

**Luồng hoạt động của Tab Ví**:
1. **Khởi tạo**: Tải danh sách địa chỉ ví và số dư
2. **Chọn ví**: Cập nhật thông tin khi chọn ví khác
3. **Tạo ví mới**: Tạo địa chỉ mới và cập nhật UI
4. **Gửi coin**: Xác thực đầu vào, kiểm tra số dư và tạo giao dịch
5. **Cập nhật lịch sử**: Hiển thị các giao dịch đã gửi/nhận

#### 3.2.2. Tab Đào Coin (`ui/mining_tab.py`)

- Hiển thị thông tin đào coin (cơ chế đồng thuận, độ khó, khối hiện tại)
- Cho phép bắt đầu/dừng quá trình đào
- Hiển thị log đào coin

**Luồng hoạt động của Tab Đào Coin**:
1. **Khởi tạo**: Hiển thị thông tin cơ chế đồng thuận và blockchain
2. **Bắt đầu đào**: Tạo thread đào coin chạy nền
3. **Quy trình đào**: 
   - PoW: Tìm nonce hợp lệ
   - PoS: Kiểm tra stake và xác định validator
4. **Cập nhật UI**: Hiển thị log về quá trình đào
5. **Broadcast khối mới**: Gửi khối đã đào đến các node khác

#### 3.2.3. Tab Mạng (`ui/network_tab.py`)

- Hiển thị thông tin mạng (IP, cổng, số node đã kết nối)
- Cho phép kết nối đến node khác
- Cho phép quét mạng LAN để tìm các node
- Hiển thị danh sách các node đã kết nối

**Luồng hoạt động của Tab Mạng**:
1. **Khởi tạo**: Hiển thị thông tin mạng hiện tại
2. **Kết nối đến node**: T��o kết nối TCP đến địa chỉ IP và cổng đã nhập
3. **Quét mạng LAN**: Tìm các node trong mạng LAN
4. **Ngắt kết nối**: Xóa node khỏi danh sách kết nối

## 4. Luồng hoạt động chính của ứng dụng

### 4.1. Khởi động và Chuẩn bị

```
[Khởi động]
    ↓
[Kiểm tra tham số dòng lệnh]
    ↓
[Tạo thư mục data nếu chưa có]
    ↓
[Khởi tạo Blockchain]
    ↓
[Tải Blockchain từ file (nếu có)]
    ↓
[Khởi tạo Wallet]
    ↓
[Tải Wallet từ file (nếu có) hoặc tạo mới]
    ↓
[Khởi tạo Network với cổng đã chỉ định]
    ↓
[Khởi động server mạng]
    ↓
[Kết nối đến node khác (nếu được chỉ định)]
    ↓
[Khởi động thread tự động lưu]
    ↓
[Khởi động giao diện người dùng]
```

### 4.2. Tạo và gửi giao dịch

```
[Người dùng chọn ví nguồn]
    ↓
[Nhập địa chỉ người nhận]
    ↓
[Nhập số lượng coin]
    ↓
[Kiểm tra số dư]
    ↓
[Tạo giao dịch]
    ↓
[Thêm vào danh sách giao dịch đang chờ]
    ↓
[Broadcast giao dịch đến các node khác]
```

### 4.3. Đào khối mới (Mining)

```
[Chọn địa chỉ nhận phần thưởng]
    ↓
[Bắt đầu đào]
    ↓
[Thêm giao dịch thưởng cho người đào]
    ↓
[Với cơ chế PoW]           [Với cơ chế PoS]
    ↓                           ↓
[Tìm nonce hợp lệ]      [Kiểm tra stake đủ không]
    ↓                           ↓
[Tạo khối mới]            [Chọn validator]
    ↓                           ↓
[Thêm vào blockchain]     [Tạo khối mới]
    ↓                           ↓
[Reset danh sách giao dịch đang chờ]
    ↓
[Broadcast khối mới]
    ↓
[Lưu blockchain]
```

### 4.4. Đồng bộ hóa blockchain với các node khác

```
[Nhận yêu cầu get_chain từ node khác]
    ↓
[Gửi blockchain hiện tại]
    ↓
[Node nhận chain]
    ↓
[So sánh độ dài với chain hiện tại]
    ↓
[Nếu chain nhận được dài hơn và hợp lệ]
    ↓
[Thay thế chain hiện tại bằng chain mới]
```

### 4.5. Nhận và xử lý khối mới

```
[Nhận khối mới từ node khác]
    ↓
[Kiểm tra tính hợp lệ của khối]
    ↓
[Nếu hợp lệ, thêm vào blockchain]
    ↓
[Xóa các giao dịch đã được xử lý khỏi pending]
    ↓
[Lưu blockchain]
```

## 5. Các luồng dữ liệu giữa các thành phần

### 5.1. Blockchain → Wallet
- Cung cấp dữ liệu giao dịch để tính số dư
- Cung cấp thông tin lịch sử giao dịch

### 5.2. Wallet → Blockchain
- Tạo giao dịch mới để thêm vào pending transactions

### 5.3. Blockchain → Network
- Cung cấp blockchain để đồng bộ với các node khác
- Cung cấp khối mới để broadcast

### 5.4. Network → Blockchain
- Cập nhật blockchain khi nhận được chain dài hơn
- Thêm khối mới khi nhận được từ node khác
- Thêm giao dịch mới khi nhận được từ node khác

### 5.5. Consensus → Blockchain
- Cung cấp quy trình đào và xác thực khối

### 5.6. UI → Core Components
- Chuyển các thao tác người dùng thành các hành động trên blockchain, wallet, network

### 5.7. Core Components → UI
- Cập nhật giao diện khi có thay đổi (số dư, khối mới, node mới)

## 6. Các cơ chế xử lý đồng thời

1. **Thread đào coin**: Chạy nền để đào các khối mới không làm đơ giao diện
2. **Thread mạng**: Lắng nghe và xử lý kết nối từ các node khác
3. **Thread kết nối**: Xử lý việc kết nối đến các node khác
4. **Thread tự động lưu**: Định kỳ lưu blockchain và wallet
5. **Thread quét mạng LAN**: Tìm kiếm các node trong mạng LAN

## 7. Lưu trữ dữ liệu

1. **blockchain.json**: Lưu trữ toàn bộ blockchain
   - Các khối đã được xác thực
   - Các giao dịch đang chờ

2. **wallet.json**: Lưu trữ thông tin ví
   - Các địa chỉ ví
   - Các khóa riêng tư
   - Địa chỉ hiện tại

## 8. Kết luận

TuCoin là một ứng dụng cryptocurrency cơ bản nhưng đầy đủ chức năng, bao gồm:
- Blockchain với đầy đủ các tính năng cơ bản
- Hỗ trợ hai cơ chế đồng thuận (PoW và PoS)
- Kết nối P2P giữa các node
- Giao diện người dùng đồ họa
- Quản lý ví và giao dịch

Ứng dụng được thiết kế theo kiến trúc module, phân tách rõ ràng giữa:
- Core components (blockchain, wallet, network, consensus)
- Giao diện ng��ời dùng (các tab wallet, mining, network)
- Lưu trữ dữ liệu (JSON)

Điều này giúp ứng dụng dễ mở rộng và bảo trì trong tương lai.