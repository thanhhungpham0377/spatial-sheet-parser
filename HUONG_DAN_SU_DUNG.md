# Hướng Dẫn Sử Dụng — Spatial Sheet Parser

**Phiên bản**: v0.1.0  
**Tác giả & Chủ sở hữu bản quyền**: Phạm Thanh Hùng (Pham Thanh Hung)  
**Bản quyền**: © 2026 Phạm Thanh Hùng. All Rights Reserved.  
**Môi trường**: Chạy Offline 100% trên máy tính cá nhân (Bảo mật tuyệt đối)

---

## 1. Khởi Động Nhanh (1 Click)
Bạn chỉ cần click đúp chuột vào tệp:
👉 **`Chay_Spatial_Sheet_Parser.bat`** ngay tại thư mục này.

Chương trình sẽ tự động:
1. Khởi động máy chủ ứng dụng cục bộ an toàn.
2. Tự động mở trình duyệt web và truy cập vào giao diện tại địa chỉ: `http://127.0.0.1:8080`.

---

## 2. Các Tính Năng Nổi Bật

### 🌐 Hỗ trợ Song Ngữ (Tiếng Việt / English)
- Góc trên cùng bên phải thanh tiêu đề có bộ chuyển đổi nhanh:
  - `[ 🇻🇳 VN ]`: Giao diện tiếng Việt chuẩn mực.
  - `[ 🇬🇧 EN ]`: Giao diện tiếng Anh chuyên nghiệp.
- Hệ thống tự động ghi nhớ ngôn ngữ bạn đã chọn cho những lần dùng tiếp theo.

### 🛡️ Bản Quyền & Bảo Mật Dữ Liệu
- Nhấn nút **`🛡️ Tác giả`** trên thanh tiêu đề để xem chứng nhận bản quyền của tác giả **Phạm Thanh Hùng**.
- Toàn bộ thuật toán nhận diện và xử lý bảng biểu đều diễn ra **100% nội bộ trên máy tính của bạn**, không gửi bất kỳ dữ liệu nào ra mạng internet, đảm bảo bí mật kinh doanh và an toàn dữ liệu.

### ⚠️ Giới Hạn Dung Lượng Tệp: 50MB
- Hỗ trợ các tệp bảng tính có dung lượng tối đa lên đến **50MB**.
- Cảnh báo trực quan hiển thị ngay tại khung tải tệp, nếu tệp vượt quá 50MB chương trình sẽ thông báo rõ ràng để bạn kịp thời điều chỉnh.

---

## 3. Cách Sử Dụng Ứng Dụng

### Bước 1: Đưa Dữ Liệu Vào
Bạn có thể chọn 1 trong 2 cách:
- **Cách 1 (Khuyên dùng)**: Kéo và thả tệp bảng tính vào khung nét đứt, hoặc bấm vào dòng **"chọn từ máy"**.
  - Định dạng hỗ trợ: Excel (`.xlsx`, `.xls`, `.xlsm`), OpenDocument (`.ods`), `.csv`, `.tsv`, `.json`.
  - Hỗ trợ chọn nhanh Sheet tính toán đối với file Excel nhiều sheet.
- **Cách 2**: Copy dữ liệu từ bảng tính (Excel hoặc Google Sheets) rồi dán trực tiếp vào ô văn bản lớn.

### Bước 2: Phân Tích Bảng Tính
- Bấm nút **`⚡ Phân tích Bảng tính`** (Analyze Sheet).
- Hệ thống sẽ hiển thị thanh tiến trình xử lý 6 giai đoạn rõ ràng và minh bạch.

### Bước 3: Xem Kết Quả & Xuất Dữ Liệu
Ứng dụng cung cấp 5 thẻ xem kết quả chi tiết:
1. **📊 Xem trước & Tổng quan (Summary Preview)**: Tổng quan trạng thái, số lượng bảng, số dòng chưa phân loại, kích thước lưới ma trận.
2. **📋 Danh mục Bảng (Table Catalog)**: Bảng thống kê toàn diện tất cả các bảng biểu và phân mục đã nhận diện (Mã bảng, Tiêu đề, Cấp độ, Bảng cha, Tọa độ vùng dữ liệu, Số dòng, Số cột, Độ tin cậy).
   - Có thanh tìm kiếm theo tên, ID, tọa độ.
   - Có bộ lọc xem: Tất cả / Chỉ Nhóm (Sections) / Bảng Cấp 1 / Bảng Con Cấp 2+ / Bảng Mồ côi.
3. **🧩 Cấu trúc & Cây Phân Cấp (Tables & Hierarchy)**: Hiển thị trực quan quan hệ Cha - Con lồng nhau giữa các bảng.
4. **📝 Văn bản Cấu trúc (Structured Text)**: Xuất ra định dạng Markdown bảng biểu có cấu trúc lồng nhau. Định dạng này **thuận nghịch 100%**, có thể khôi phục lại bảng bất kỳ lúc nào để chuyển giao sang ứng dụng khác hoặc đưa vào LLM/AI.
5. **{ } Dữ liệu JSON**: Định dạng chuẩn kỹ thuật có cấu trúc đầy đủ, có nút sao chép (Copy JSON) và tải về (Download JSON).

---

## 4. Cấu Trúc Thư Mục Gọn Gàng
- `Chay_Spatial_Sheet_Parser.bat`: File nhấp đúp để khởi động ứng dụng ngay lập tức.
- `HUONG_DAN_SU_DUNG.md`: Tài liệu hướng dẫn sử dụng tiếng Việt.
- `dist/spatial-sheet-parser.exe`: Tệp thực thi độc lập cho Windows (đã ký thông tin bản quyền của Phạm Thanh Hùng).
- `src/`: Mã nguồn phần mềm.
- `tests/`: Bộ kiểm thử tự động đảm bảo độ ổn định và chính xác.
- `packaging/`: Cấu hình đóng gói tệp thực thi Windows.

---
*Chúc bạn có trải nghiệm làm việc hiệu quả với Spatial Sheet Parser!*
