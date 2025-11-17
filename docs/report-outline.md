"Thành viên nhóm 1:
1. Nguyễn Tấn Lộc
2. Cù Bảo Tiệp
3. Nguyễn Phan Hải Âu
4. Trần Hữu Thành Đạt
5. Nguyễn Hữu Tuấn


" PHẦN 1: TỔNG QUAN VỀ GIAO THỨC UDP
1.1. Khái niệm
UDP (User Datagram Protocol) là một giao thức cốt lõi trong bộ giao thức Internet (IP). Khác với TCP chú trọng vào sự tin cậy, UDP là một giao thức không kết nối (connectionless). Nó hoạt động theo cơ chế "Fire and Forget" (Gửi và Quên), nghĩa là gửi gói tin đi mà không cần thiết lập kết nối trước và không đảm bảo gói tin sẽ đến nơi.

1.2. Đặc điểm kỹ thuật

Không tin cậy (Unreliable): Không có cơ chế xác nhận (ACK), không gửi lại gói tin bị mất, không đảm bảo thứ tự gói tin.


Header nhỏ gọn: UDP header chỉ có kích thước 8 bytes, nhẹ hơn rất nhiều so với 20 bytes của TCP. Điều này giúp giảm băng thông tiêu tốn cho các thông tin quản lý (overhead).


Tốc độ cao: Do không mất thời gian bắt tay 3 bước và không có các thuật toán kiểm soát tắc nghẽn phức tạp, UDP có độ trễ (latency) thấp hơn TCP.

PHẦN 2: CÁC VẤN ĐỀ HIỆU NĂNG CỦA UDP
Mặc dù UDP nhanh, nhưng "nhanh" không có nghĩa là "tối ưu". Khi lập trình ứng dụng UDP thực tế, ta thường gặp các vấn đề sau:


Packet Loss (Mất gói): Khi mạng bị nghẽn hoặc bộ đệm (buffer) của máy nhận bị đầy, gói tin sẽ bị vứt bỏ (drop) không thương tiếc.

Fragmentation (Phân mảnh): Nếu gửi gói tin quá lớn vượt quá MTU (Maximum Transmission Unit), nó sẽ bị chia nhỏ. Nếu một mảnh nhỏ bị mất, toàn bộ gói tin lớn sẽ hỏng.

Out-of-order (Sai thứ tự): Gói tin gửi sau có thể đến trước.

PHẦN 3: CÁC KỸ THUẬT TỐI ƯU HÓA UDP
Để tối ưu hóa UDP, chúng ta không can thiệp vào giao thức (vì nó đã cố định), mà can thiệp vào cách sử dụng (Application Layer) và cấu hình hệ thống (Kernel Level).

3.1. Tối ưu hóa mức Hệ thống (Kernel Level)
a. Điều chỉnh kích thước Buffer (Socket Buffer Sizing)
Mặc định, bộ nhớ đệm nhận (Receive Buffer) của hệ điều hành có thể khá nhỏ. Nếu ứng dụng không kịp xử lý dữ liệu đến, buffer sẽ đầy và gói tin mới sẽ bị drop.


Giải pháp: Tăng kích thước SO_RCVBUF (Receive Buffer) và SO_SNDBUF (Send Buffer) lên mức cao hơn.

Ví dụ (Python):

Python

sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024) # Tăng lên 1MB
b. Sử dụng Batch Processing (Gửi/Nhận theo lô)
Việc gọi lệnh send() hoặc recv() cho từng gói tin nhỏ gây tốn kém tài nguyên CPU (do chuyển đổi giữa User mode và Kernel mode).

Giải pháp: Sử dụng các system call đặc biệt để gửi/nhận nhiều gói tin một lúc. Trên Linux, đó là sendmmsg và recvmmsg. Điều này giúp giảm tải CPU đáng kể khi truyền tải lượng lớn dữ liệu.

c. SO_REUSEPORT (Đa luồng)
Giải pháp: Cho phép nhiều process hoặc thread cùng lắng nghe trên một cổng (port) duy nhất. Kernel sẽ tự động phân phối tải (load balancing) các gói tin đến cho các thread này, tận dụng sức mạnh của CPU đa nhân.

3.2. Tối ưu hóa mức Ứng dụng (Application Layer)
a. Tránh phân mảnh (Avoid IP Fragmentation)
MTU (Maximum Transmission Unit) phổ biến trên Internet là 1500 bytes. Trừ đi header của IP (20 bytes) và UDP (8 bytes), kích thước dữ liệu tối đa an toàn là 1472 bytes.

Tối ưu: Luôn giữ kích thước gói tin (payload) dưới 1472 bytes (thường khuyến nghị khoảng 1400 bytes để an toàn qua các VPN/Tunnel). Việc này tránh cho router phải tốn công chia nhỏ gói tin và giảm rủi ro mất mát.

b. Triển khai độ tin cậy ở lớp ứng dụng (Reliable UDP - RUDP)
Nếu bạn cần tốc độ của UDP nhưng không muốn mất dữ liệu quan trọng, bạn phải tự code cơ chế tin cậy.

Cơ chế: Tự thêm số thứ tự (Sequence Number) vào gói tin và yêu cầu bên nhận gửi xác nhận (ACK) cho các gói quan trọng.

Công nghệ tiêu biểu:

QUIC (HTTP/3): Google phát triển trên nền UDP. Nó giải quyết vấn đề tắc nghẽn và mất gói tốt hơn TCP, hiện đang là nền tảng của web hiện đại.


WebRTC: Dùng cho video call, sử dụng UDP nhưng có các cơ chế kiểm soát bitrate để đảm bảo chất lượng video.

c. Pacing (Điều tiết tốc độ gửi)
Do UDP không có Flow Control, nếu gửi quá nhanh, bạn sẽ tự làm ngập đường truyền hoặc làm tràn bộ đệm của người nhận.

Tối ưu: Cài đặt cơ chế "Pacing" ở ứng dụng gửi. Ví dụ: Chỉ gửi 1000 gói/giây, nếu thấy mạng lag thì tự động giảm xuống.

PHẦN 4: KẾT LUẬN
Giao thức UDP là lựa chọn số một cho các ứng dụng thời gian thực nhờ sự đơn giản và tốc độ. Tuy nhiên, để sử dụng UDP hiệu quả trong môi trường production, lập trình viên không thể chỉ dùng các hàm sendto/recvfrom cơ bản. Việc áp dụng các kỹ thuật tối ưu như điều chỉnh kích thước buffer, giữ kích thước gói tin dưới MTU, và đặc biệt là sử dụng các giao thức hiện đại trên nền UDP như QUIC là chìa khóa để đạt hiệu năng cao nhất.