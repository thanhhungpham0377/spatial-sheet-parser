# Spatial Sheet Parser — Product Specification

## 1. Mục tiêu

Xây dựng ứng dụng nhận ma trận dữ liệu từ Google Sheets/TSV/CSV, nhận diện mục lục, vùng dữ liệu, các bảng phân cấp theo vị trí cột, sau đó xuất JSON chuẩn hóa nhưng vẫn truy nguyên được vị trí dữ liệu gốc.

## 2. Nguyên tắc sản phẩm

- Không tự bịa, làm tròn hoặc thay đổi giá trị nguồn.
- Ưu tiên parser deterministic; AI chỉ là fallback cho trường hợp mơ hồ.
- Mọi nhận diện không chắc chắn phải có `confidence` và `warnings`.
- Không âm thầm bỏ dữ liệu: phải báo các ô/dòng không được phân loại.
- Có preview để người dùng sửa vùng, title, header và quan hệ cha-con trước khi export.

## 3. Phạm vi MVP

- Một sheet mỗi lần phân tích.
- Input: TSV paste, CSV upload, JSON grid; Google Sheets API là phase kế tiếp.
- Title ở các cột cấu hình được, mặc định A/B/C.
- Bảng có một dòng header và vùng record dạng dọc.
- Table anchor mặc định là title column + 1.
- Hỗ trợ TOC, data marker `[BEGIN DATA]`, merged-cell policy `top_left_only`.
- Xuất JSON, copy JSON và hiển thị cảnh báo.

## 4. Mô hình xử lý

```text
Input adapter → Normalize grid → Detect regions → Detect table candidates
→ Detect headers/records → Build hierarchy → Validate → Preview → Export JSON
```

## 5. Quy tắc nhận diện

### 5.1 Table title

Một candidate cần có giá trị tại title column và nên thỏa ít nhất hai bằng chứng: dòng kế tiếp có header ở anchor column; có record sau header; có style title; có marker `[TABLE]`; hoặc có dữ liệu liên tục trong vùng anchor.

Các dòng `Tổng cộng`, `Ghi chú`, `Người lập`, footer và dòng chỉ có một ô không có dữ liệu kế tiếp không được tự động xem là bảng.

### 5.2 Hierarchy

- Level mặc định = title column index.
- Parent là bảng gần nhất trước đó có level thấp hơn.
- Nếu nhảy cấp, không tạo node giả; gắn vào ancestor gần nhất và warning `LEVEL_SKIPPED`.
- Bảng không có parent nằm trong `orphan_tables`.

### 5.3 Table range

Lưu `title_cell`, `data_range`, `header_row`, `record_start_row`, `record_end_row`.
Không kết thúc chỉ vì một dòng trống đơn lẻ; dùng `max_blank_rows` cấu hình được. Kết thúc khi gặp title mới cùng hoặc thấp hơn level, marker mới, hoặc bằng chứng chuyển vùng đủ mạnh.

### 5.4 Header và giá trị

Header label tách khỏi JSON key. Header trùng phải tạo key ổn định duy nhất. Nếu nguồn chỉ là text/CSV, mặc định giữ giá trị dạng string; chỉ gán type khi adapter cung cấp kiểu chắc chắn.

## 6. JSON contract

```json
{
  "metadata": {
    "parser_version": "1.0.0",
    "source_format": "tsv",
    "sheet_name": null,
    "toc_summary": [],
    "data_start_row": 0,
    "warnings": []
  },
  "tables": [],
  "orphan_tables": [],
  "unclassified_rows": []
}
```

Mỗi table tối thiểu có: `table_id`, `title`, `level`, `parent_id`, `title_cell`, `anchor_column`, `data_range`, `header_row`, `record_start_row`, `record_end_row`, `columns`, `records`, `children`, `confidence`, `warnings`.

## 7. Warning codes

`AMBIGUOUS_TABLE_TITLE`, `MISSING_HEADER`, `EMPTY_RECORDS`, `DUPLICATE_HEADER`, `LEVEL_SKIPPED`, `ORPHAN_TABLE`, `UNEXPECTED_BLANK_ROW`, `POSSIBLE_FOOTER`, `MERGED_CELL_DETECTED`, `TRUNCATED_TABLE`, `UNCLASSIFIED_DATA`.

## 8. Cấu hình

```json
{
  "title_columns": [0, 1, 2],
  "table_offset": 1,
  "max_blank_rows": 1,
  "header_rows": 1,
  "explicit_markers": ["[BEGIN DATA]", "[TABLE]"],
  "merged_cell_policy": "top_left_only",
  "strictness": "balanced"
}
```

## 9. Phi chức năng

- Deterministic và tái lập được với cùng input/config.
- Không log dữ liệu nhạy cảm nguyên văn ngoài chế độ debug.
- Parser core không phụ thuộc UI.
- Có test cho happy path, malformed input, duplicate header, blank rows, level jump, orphan và merged cell.
- Schema/versioning phải cho phép nâng cấp tương thích.

## 10. Không thuộc MVP

OAuth Google, ghi ngược vào Sheets, bảng ngang phức tạp, chỉnh sửa style gốc, AI tự động không kiểm soát, multi-sheet join và triển khai production cloud.
