# Đề cương báo cáo: Tối ưu hóa giao thức UDP

## 1. Tổng quan về UDP
- **Khái niệm:** UDP (User Datagram Protocol) là giao thức không kết nối, hoạt động theo cơ chế "gửi và quên" nên không đảm bảo gói tin tới đích hoặc đúng thứ tự.
- **Đặc điểm kỹ thuật:**
  - Header nhỏ gọn (8 bytes) giúp giảm overhead so với TCP.
  - Không có cơ chế ACK/ retransmission nên độ trễ thấp nhưng không tin cậy.
  - Phù hợp cho ứng dụng thời gian thực như game, VoIP, video streaming.

## 2. Các vấn đề hiệu năng thường gặp
- **Mất gói (Packet loss):** bộ đệm nhận đầy, mạng nghẽn hoặc router drop gói.
- **Phân mảnh IP (Fragmentation):** gói vượt MTU bị chia nhỏ; chỉ cần mất một mảnh là cả gói hỏng.
- **Sai thứ tự (Out-of-order):** gói gửi sau có thể đến trước, ứng dụng phải tự sắp xếp.

## 3. Kỹ thuật tối ưu hóa
### 3.1 Mức hệ thống (Kernel level)
- **Điều chỉnh kích thước buffer:** tăng `SO_RCVBUF` và `SO_SNDBUF` để tránh drop khi tải cao.
- **Batch I/O:** dùng `recvmmsg`/`sendmmsg` để nhận/gửi nhiều gói trong một syscall, giảm overhead chuyển chế độ.
- **SO_REUSEPORT:** cho phép nhiều worker cùng lắng nghe một port, kernel tự cân bằng tải giữa các CPU core.

### 3.2 Mức ứng dụng
- **Tránh phân mảnh:** giữ payload < 1400 bytes (dưới ngưỡng MTU 1500 trừ header IP/UDP).
- **Độ tin cậy tầng ứng dụng:** thêm sequence number + ACK hoặc dùng giao thức trên nền UDP như QUIC/WebRTC.
- **Pacing/Rate limiting:** giới hạn tốc độ gửi để không làm nghẽn đường truyền hoặc tràn buffer.

## 4. Minh họa trong mã nguồn
- `src/baseline/`: UDP echo cơ bản và client đo RTT/loss.
- `src/asyncio/`: dùng `asyncio.DatagramProtocol` để tăng throughput mà không cần nhiều thread.
- `src/opt_buffers/`: tăng buffer, dùng batch I/O và zero-copy (memoryview) để giảm chi phí hệ thống.

## 5. Kết luận
UDP mang lại độ trễ thấp nhưng cần cấu hình và kiểm soát ở tầng ứng dụng để đạt hiệu năng ổn định. Các kỹ thuật trên giúp giảm mất gói, tránh phân mảnh và khai thác tối đa tài nguyên CPU.
