# Spatial Sheet Parser — Task Queue

## Operating rules

- Chạy đúng một task Antigravity tại một thời điểm.
- Antigravity chỉ sửa trong Write Scope; Codex review và closeout.
- Không tự sửa TODO/CHANGELOG bởi Antigravity.
- Model bắt buộc: `Gemini 3.6 Flash (High)`.

## Task Run Manifest

| Task | Executor | Depends on | Write Scope | Status |
|---|---|---|---|---|
| SSP-001 | Antigravity | none | `README.md`, `docs/ARCHITECTURE.md`, `pyproject.toml` hoặc runtime manifest phù hợp | ready |
| SSP-002 | Antigravity | SSP-001 | `src/`, `tests/` parser core only | queued |
| SSP-003 | Antigravity | SSP-002 | `src/`, `tests/` validation/schema only | queued |
| SSP-004 | Antigravity | SSP-003 | `src/`, `tests/`, `ui/` preview/export only | queued |
| SSP-005 | Antigravity | SSP-004 | `tests/`, `docs/`, README test instructions | queued |

## SSP-001 — Bootstrap architecture

**Goal:** tạo skeleton chạy được, chọn runtime tối giản, định nghĩa module boundaries và CLI/API contract.

**Acceptance:** có README, architecture doc, lệnh test/lint cơ bản, fixture format; không triển khai parser đầy đủ.

## SSP-002 — Deterministic parser core

**Goal:** normalize grid, detect TOC/data, title/header/records, hierarchy, ranges, merged policy.

**Acceptance:** parser thuần code, có unit tests cho MVP rules và không làm mất dòng/ô mà không warning.

## SSP-003 — Contract and validation

**Goal:** JSON contract, stable column keys, warnings, confidence, unclassified rows, validation.

**Acceptance:** JSON hợp lệ, deterministic, negative tests và schema/version test.

## SSP-004 — Preview and export surface

**Goal:** giao diện hoặc CLI preview hiển thị vùng nhận diện, warnings và export JSON; chọn phương án phù hợp với skeleton.

**Acceptance:** người dùng xem được kết quả, có thể chọn/cấu hình input cơ bản, export được artifact.

## SSP-005 — Integration hardening

**Goal:** fixture thực tế, regression suite, docs sử dụng, kiểm tra performance và edge cases.

**Acceptance:** test suite pass, docs chạy được từ workspace sạch, báo rõ giới hạn MVP.
