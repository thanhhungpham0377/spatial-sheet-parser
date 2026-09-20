@echo off
chcp 65001 >nul
title Spatial Sheet Parser - Pham Thanh Hung

echo ======================================================================
echo          SPATIAL SHEET PARSER - HEIRARCHY DETECTOR v0.1.0
echo             Tác giả & Bản quyền: Phạm Thanh Hùng (c) 2026
echo ======================================================================
echo.
echo [1/3] Đang khởi chạy ứng dụng Spatial Sheet Parser...
echo.

cd /d "%~dp0"

REM Kiểm tra nếu có tệp EXE trong thư mục dist thì chạy trực tiếp
if exist "dist\spatial-sheet-parser.exe" (
    echo [*] Khởi động tệp thực thi Windows: dist\spatial-sheet-parser.exe
    start "" "dist\spatial-sheet-parser.exe"
) else if exist ".venv\Scripts\python.exe" (
    echo [*] Khởi động ứng dụng thông qua môi trường ảo Python...
    start "" ".venv\Scripts\python.exe" -m spatial_sheet_parser.launcher
) else (
    echo [!] Không tìm thấy tệp EXE hoặc môi trường ảo Python!
    echo Vui lòng liên hệ tác giả Phạm Thanh Hùng hoặc kiểm tra lại thư mục cài đặt.
    pause
    exit /b 1
)

echo [2/3] Chờ máy chủ khởi động trong 2 giây...
timeout /t 2 /nobreak >nul

echo [3/3] Tự động mở giao diện ứng dụng trên trình duyệt web...
start http://127.0.0.1:8080

echo.
echo ======================================================================
echo   Ứng dụng đang chạy tại: http://127.0.0.1:8080
echo   Toàn bộ dữ liệu được xử lý 100%% offline, an toàn và bảo mật.
echo   Giới hạn dung lượng tệp tối đa: 50MB.
echo ======================================================================
echo.
echo Bạn có thể thu nhỏ cửa sổ này lại khi đang sử dụng.
pause
