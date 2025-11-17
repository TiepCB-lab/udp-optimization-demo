# UDP Optimization Demo

## Mục tiêu
Dự án mô phỏng và minh họa các kỹ thuật tối ưu hóa giao thức UDP 
nhằm tăng hiệu suất truyền thông, giảm độ trễ và hạn chế mất gói trong quá trình giao tiếp giữa client và server.

## Cấu trúc thư mục
UDP-OPTIMIZATION-DEMO/
│
├─ src/
│ ├─ baseline/ # UDP cơ bản
│ │ ├─ server_baseline.py
│ │ └─ client_baseline.py
│ │
│ ├─ asyncio/ # UDP bất đồng bộ (asyncio)
│ │ ├─ server_asyncio.py
│ │ └─ client_asyncio.py
│ │
│ └─ opt_buffers/ # UDP tối ưu buffer và zero-copy
│ ├─ server_optbuf.py
│ └─ client_optbuf.py
│
├─ docs/
│ └─ report-outline.md # dàn ý báo cáo
│
├─ requirements.txt # thư viện cần thiết
├─ README.md # tài liệu hướng dẫn
└─ LICENSE