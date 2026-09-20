// Spatial Sheet Parser - Local Web App JavaScript Engine (SSP-011 Hardened)

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const fileInput = document.getElementById("file-input");
    const dropZone = document.getElementById("drop-zone");
    const fileNameDisplay = document.getElementById("file-name-display");
    const fileMetadataPanel = document.getElementById("file-metadata-panel");
    const metaFilename = document.getElementById("meta-filename");
    const metaSize = document.getElementById("meta-size");
    const metaFormat = document.getElementById("meta-format");
    const metaMode = document.getElementById("meta-mode");
    const metaClearBtn = document.getElementById("meta-clear-btn");

    const inputText = document.getElementById("input-text");
    const formatSelect = document.getElementById("format-select");
    const sheetNameInput = document.getElementById("sheet-name-input");
    const sheetSelect = document.getElementById("sheet-select");
    const sheetLabel = document.getElementById("sheet-label");
    const analyzeBtn = document.getElementById("analyze-btn");
    const clearBtn = document.getElementById("clear-btn");
    const copyJsonBtn = document.getElementById("copy-json-btn");
    const downloadJsonBtn = document.getElementById("download-json-btn");
    const copyMdBtn = document.getElementById("copy-md-btn");
    const downloadMdBtn = document.getElementById("download-md-btn");

    const errorBanner = document.getElementById("error-banner");
    const errorMessage = document.getElementById("error-message");
    const closeErrorBtn = document.getElementById("close-error-btn");
    const copyErrorBtn = document.getElementById("copy-error-btn");
    const errorDetailsContent = document.getElementById("error-details-content");

    const loadingOverlay = document.getElementById("loading-overlay");
    const progressTitle = document.getElementById("progress-title");
    const progressStepText = document.getElementById("progress-step-text");
    const progressBarFill = document.getElementById("progress-bar-fill");
    const cancelAnalyzeBtn = document.getElementById("cancel-analyze-btn");

    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    // Header, Language Switcher & About Modal elements
    const langBtnVi = document.getElementById("lang-btn-vi");
    const langBtnEn = document.getElementById("lang-btn-en");
    const aboutBtn = document.getElementById("about-btn");
    const aboutModal = document.getElementById("about-modal");
    const closeAboutBtn = document.getElementById("close-about-btn");
    const closeAboutActionBtn = document.getElementById("close-about-action-btn");

    const previewOutput = document.getElementById("preview-output");
    const jsonOutput = document.getElementById("json-output");
    const summaryMetrics = document.getElementById("summary-metrics");

    // Markdown tab elements
    const markdownEmpty = document.getElementById("markdown-empty");
    const markdownContent = document.getElementById("markdown-content");
    const markdownOutput = document.getElementById("markdown-output");

    // Catalog tab elements
    const catalogEmpty = document.getElementById("catalog-empty");
    const catalogContent = document.getElementById("catalog-content");
    const catalogTableBody = document.getElementById("catalog-table-body");
    const catalogSearchInput = document.getElementById("catalog-search-input");
    const catalogLevelFilter = document.getElementById("catalog-level-filter");
    const catalogCountBadge = document.getElementById("catalog-count-badge");

    // Metrics elements
    const metricStatus = document.getElementById("metric-status");
    const metricFormat = document.getElementById("metric-format");
    const metricSheet = document.getElementById("metric-sheet");
    const metricDims = document.getElementById("metric-dims");
    const metricTables = document.getElementById("metric-tables");
    const metricOrphans = document.getElementById("metric-orphans");
    const metricWarnings = document.getElementById("metric-warnings");
    const metricUnclassified = document.getElementById("metric-unclassified");

    // Details elements
    const detailsEmpty = document.getElementById("details-empty");
    const detailsContent = document.getElementById("details-content");
    const tablesList = document.getElementById("tables-list");
    const orphansSection = document.getElementById("orphans-section");
    const orphansList = document.getElementById("orphans-list");
    const warningsSection = document.getElementById("warnings-section");
    const warningsList = document.getElementById("warnings-list");
    const unclassifiedSection = document.getElementById("unclassified-section");
    const unclassifiedList = document.getElementById("unclassified-list");

    // State Variables
    let currentResult = null;
    let currentPreview = "";
    let currentMarkdown = "";
    let currentFile = null;
    let uploadedBase64 = null;
    let isBinaryFile = false;
    let lastErrorDetails = "";
    let currentAbortController = null;
    let currentRequestId = null;

    // -------------------------------------------------------------
    // Internationalization (I18N) - Song ngữ EN / VN
    // -------------------------------------------------------------
    const I18N = {
        vi: {
            authorBtn: "Tác giả",
            copyError: "📋 Sao chép lỗi",
            technicalDetails: "Chi tiết kỹ thuật",
            inputTitle: "Dữ liệu Bảng tính Đầu vào",
            inputSubtitle: "Tải tệp lên hoặc dán ma trận TSV / CSV / JSON",
            dropText: "Kéo & thả tệp Excel (.xlsx, .xls, Google Sheets), OpenDocument (.ods), TSV, CSV, hoặc JSON vào đây, hoặc ",
            browseLink: "chọn từ máy",
            dropLimitNotice: "Lưu ý: Dung lượng tệp tối đa được hỗ trợ là 50MB. Dữ liệu xử lý hoàn toàn ngoại tuyến & bảo mật.",
            fileMetaTitle: "📄 Thông tin Tệp đã chọn",
            removeFile: "Xóa tệp",
            metaFilenameLabel: "Tên tệp:",
            metaSizeLabel: "Dung lượng:",
            metaFormatLabel: "Định dạng:",
            metaModeLabel: "Chế độ tải:",
            dividerOr: "HOẶC DÁN VĂN BẢN TRỰC TIẾP",
            inputPlaceholder: "Dán ma trận dữ liệu bảng tính của bạn vào đây (TSV, CSV, hoặc JSON)...",
            formatSelectLabel: "Định dạng nguồn",
            formatAuto: "Tự động phát hiện (Auto)",
            sheetNameLabel: "Tên trang tính / Sheet (Tùy chọn)",
            sheetNamePlaceholder: "Ví dụ: BangLuong",
            analyzeBtn: "Phân tích Bảng tính",
            clearBtn: "Xóa",
            tabSummary: "Xem trước & Tổng quan",
            tabCatalog: "Danh mục Bảng (Catalog)",
            tabDetails: "Cấu trúc & Cây phân cấp",
            tabMarkdown: "Văn bản Cấu trúc",
            tabJson: "Dữ liệu JSON",
            copyJsonBtn: "Sao chép JSON",
            downloadJsonBtn: "Tải JSON",
            copyMdBtn: "Sao chép Markdown",
            downloadMdBtn: "Tải .md",
            metricStatus: "Trạng thái",
            metricFormat: "Định dạng",
            metricSheet: "Trang tính",
            metricDims: "Kích thước",
            metricTables: "Số bảng",
            metricOrphans: "Bảng mồ côi",
            metricWarnings: "Cảnh báo",
            metricUnclassified: "Dòng chưa định danh",
            catalogEmptyText: "Chưa có bảng nào được nhận diện. Vui lòng bấm \"Phân tích Bảng tính\" để xem danh mục bảng.",
            filterAll: "Tất cả các Cấp & Bảng",
            filterSections: "📁 Chỉ Nhóm / Phân mục (Categories)",
            filterRoot: "Chỉ Bảng Gốc (Cấp 1)",
            filterSub: "Chỉ Bảng Con (Cấp 2+)",
            filterOrphans: "Chỉ Bảng Mồ côi (Orphan)",
            catalogSearchPlaceholder: "Tìm kiếm bảng theo tiêu đề, mã ID, hoặc tọa độ...",
            thTableId: "Mã Bảng",
            thTitle: "Tiêu đề Bảng & Cấu trúc Phân cấp",
            thLevel: "Cấp độ",
            thParentId: "Bảng Cha",
            thDataRange: "Vùng Dữ liệu",
            thRecords: "Số dòng",
            thCols: "Số cột",
            thConfidence: "Độ tin cậy",
            detailsEmptyText: "Chưa có kết quả phân tích. Hãy chạy phân tích để kiểm tra ranh giới bảng.",
            secTablesTitle: "Cây Phân cấp Bảng Biểu đã Nhận diện",
            secOrphansTitle: "Bảng Mồ côi (Không có bảng cha)",
            secWarningsTitle: "Cảnh báo Toàn cục",
            secUnclassTitle: "Dòng Không Thuộc Bảng (Tránh thất thoát thông tin)",
            markdownEmptyText: "Kết quả văn bản cấu trúc sẽ hiển thị ở đây. Định dạng này có tính thuận nghịch 100% — có thể khôi phục lại bảng bất cứ lúc nào.",
            footerDev: "Phát triển bởi",
            footerRights: "Tất cả các quyền được bảo lưu.",
            aboutTitle: "Thông tin Tác giả & Bản quyền",
            authorRole: "Tác giả & Chủ sở hữu bản quyền phần mềm",
            aboutSoftware: "Phần mềm:",
            aboutLicense: "Bản quyền:",
            aboutNotice: "Bảo mật & Dung lượng:",
            aboutLimitDesc: "Hỗ trợ kích thước tệp tối đa 50MB. Dữ liệu xử lý hoàn toàn 100% ngoại tuyến (offline) trên máy tính của bạn, đảm bảo tuyệt đối an toàn và bảo mật dữ liệu riêng tư.",
            closeBtn: "Đóng",
            cancelBtn: "Hủy Phân tích",
            fileTooLargeMsg: "Tệp vượt quá giới hạn dung lượng tối đa cho phép là 50MB. Vui lòng chọn tệp nhỏ hơn.",
            noDataMsg: "Vui lòng nhập hoặc tải tệp dữ liệu bảng tính trước khi bấm Phân tích.",
            analyzingTitle: "Đang phân tích Lưới Ma trận Không gian...",
            copiedJsonSuccess: "Đã sao chép toàn bộ kết quả JSON vào clipboard!",
            copiedMdSuccess: "Đã sao chép toàn bộ nội dung Markdown vào clipboard!",
            step1: "Đọc tệp dữ liệu",
            step2: "Chuẩn bị tải lên",
            step3: "Đang tải dữ liệu",
            step4: "Phân tích bảng tính",
            step5: "Xây dựng kết quả",
            step6: "Hoàn tất"
        },
        en: {
            authorBtn: "Author",
            copyError: "📋 Copy error",
            technicalDetails: "Technical Details",
            inputTitle: "Input Sheet Data",
            inputSubtitle: "Upload file or paste TSV / CSV / JSON matrix",
            dropText: "Drag & drop Excel (.xlsx, .xls, Google Sheets export), OpenDocument (.ods), TSV, CSV, or JSON file here, or ",
            browseLink: "browse",
            dropLimitNotice: "Max supported file size: 50MB. All processing is 100% offline & private.",
            fileMetaTitle: "📄 Selected File Metadata",
            removeFile: "Remove file",
            metaFilenameLabel: "Filename:",
            metaSizeLabel: "File Size:",
            metaFormatLabel: "Format:",
            metaModeLabel: "Payload Mode:",
            dividerOr: "OR PASTE TEXT DIRECTLY",
            inputPlaceholder: "Paste your spreadsheet matrix data here (TSV, CSV, or JSON)...",
            formatSelectLabel: "Source Format",
            formatAuto: "Auto-detect",
            sheetNameLabel: "Sheet Name (Optional)",
            sheetNamePlaceholder: "e.g. SalesSummary",
            analyzeBtn: "Analyze Sheet",
            clearBtn: "Clear",
            tabSummary: "Summary Preview",
            tabCatalog: "Table Catalog",
            tabDetails: "Tables & Hierarchy",
            tabMarkdown: "Structured Text",
            tabJson: "JSON Output",
            copyJsonBtn: "Copy JSON",
            downloadJsonBtn: "Download JSON",
            copyMdBtn: "Copy Markdown",
            downloadMdBtn: "Download .md",
            metricStatus: "Status",
            metricFormat: "Format",
            metricSheet: "Sheet",
            metricDims: "Grid Size",
            metricTables: "Tables",
            metricOrphans: "Orphans",
            metricWarnings: "Warnings",
            metricUnclassified: "Unclassified",
            catalogEmptyText: "No tables detected yet. Run analysis to see the full catalog and summary table of all detected regions.",
            filterAll: "All Levels & Tables",
            filterSections: "📁 Sections Only (Categories)",
            filterRoot: "Root Tables Only (Level 1)",
            filterSub: "Sub-tables Only (Level 2+)",
            filterOrphans: "Orphan Tables Only",
            catalogSearchPlaceholder: "Search tables by title, ID, or range...",
            thTableId: "Table ID",
            thTitle: "Table Title & Hierarchy",
            thLevel: "Level",
            thParentId: "Parent ID",
            thDataRange: "Data Range",
            thRecords: "Records",
            thCols: "Cols",
            thConfidence: "Confidence",
            detailsEmptyText: "No analysis results available yet. Run analysis to inspect detected tables and boundaries.",
            secTablesTitle: "Detected Hierarchical Tables",
            secOrphansTitle: "Orphan Tables (No Parent)",
            secWarningsTitle: "Global Warnings",
            secUnclassTitle: "Unclassified Rows (Traceability Loss Prevention)",
            markdownEmptyText: "Structured text output will appear here after parsing. This format is reversible — it can be parsed back into tables.",
            footerDev: "Developed by",
            footerRights: "All Rights Reserved.",
            aboutTitle: "Author & Copyright Information",
            authorRole: "Author & Software Copyright Owner",
            aboutSoftware: "Software:",
            aboutLicense: "Copyright:",
            aboutNotice: "Security & Limit:",
            aboutLimitDesc: "Supports up to 50MB. All data processing is 100% offline on your machine, ensuring full privacy and data security.",
            closeBtn: "Close",
            cancelBtn: "Cancel Analysis",
            fileTooLargeMsg: "File exceeds the maximum allowed limit of 50MB. Please choose a smaller file.",
            noDataMsg: "Please provide spreadsheet text or upload a file first.",
            analyzingTitle: "Analyzing Spatial Grid Matrix...",
            copiedJsonSuccess: "Copied full JSON contract to clipboard!",
            copiedMdSuccess: "Copied structured Markdown to clipboard!",
            step1: "Reading file",
            step2: "Preparing upload",
            step3: "Uploading",
            step4: "Parsing workbook",
            step5: "Building result",
            step6: "Completed"
        }
    };

    let currentLang = "vi";
    try {
        if (typeof localStorage !== "undefined") {
            const savedLang = localStorage.getItem("spatial_sheet_parser_lang");
            if (savedLang === "en" || savedLang === "vi") {
                currentLang = savedLang;
            }
        }
    } catch (_) {}

    const STEP_NAMES = {
        1: I18N[currentLang].step1,
        2: I18N[currentLang].step2,
        3: I18N[currentLang].step3,
        4: I18N[currentLang].step4,
        5: I18N[currentLang].step5,
        6: I18N[currentLang].step6
    };

    function setLanguage(lang) {
        if (!I18N[lang]) return;
        currentLang = lang;
        try {
            if (typeof localStorage !== "undefined") {
                localStorage.setItem("spatial_sheet_parser_lang", lang);
            }
        } catch (_) {}

        if (langBtnVi && langBtnVi.classList) {
            if (lang === "vi") langBtnVi.classList.add("active");
            else langBtnVi.classList.remove("active");
        }
        if (langBtnEn && langBtnEn.classList) {
            if (lang === "en") langBtnEn.classList.add("active");
            else langBtnEn.classList.remove("active");
        }

        const dict = I18N[lang];
        if (typeof document.querySelectorAll === "function") {
            const elementsToTranslate = document.querySelectorAll("[data-i18n]");
            if (elementsToTranslate && typeof elementsToTranslate.forEach === "function") {
                elementsToTranslate.forEach(el => {
                    const key = el.getAttribute("data-i18n");
                    if (dict[key]) {
                        el.textContent = dict[key];
                    }
                });
            }
        }

        if (inputText) inputText.placeholder = dict.inputPlaceholder;
        if (sheetNameInput) sheetNameInput.placeholder = dict.sheetNamePlaceholder;
        if (catalogSearchInput) catalogSearchInput.placeholder = dict.catalogSearchPlaceholder;

        STEP_NAMES[1] = dict.step1;
        STEP_NAMES[2] = dict.step2;
        STEP_NAMES[3] = dict.step3;
        STEP_NAMES[4] = dict.step4;
        STEP_NAMES[5] = dict.step5;
        STEP_NAMES[6] = dict.step6;
    }

    if (langBtnVi) langBtnVi.addEventListener("click", () => setLanguage("vi"));
    if (langBtnEn) langBtnEn.addEventListener("click", () => setLanguage("en"));

    if (aboutBtn) {
        aboutBtn.addEventListener("click", () => {
            if (aboutModal && aboutModal.classList) aboutModal.classList.remove("hidden");
        });
    }
    if (closeAboutBtn) {
        closeAboutBtn.addEventListener("click", () => {
            if (aboutModal && aboutModal.classList) aboutModal.classList.add("hidden");
        });
    }
    if (closeAboutActionBtn) {
        closeAboutActionBtn.addEventListener("click", () => {
            if (aboutModal && aboutModal.classList) aboutModal.classList.add("hidden");
        });
    }
    if (aboutModal) {
        aboutModal.addEventListener("click", (e) => {
            if (e.target === aboutModal && aboutModal.classList) {
                aboutModal.classList.add("hidden");
            }
        });
    }
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && aboutModal && aboutModal.classList && !aboutModal.classList.contains("hidden")) {
            aboutModal.classList.add("hidden");
        }
    });

    // Apply initial language
    setLanguage(currentLang);

    // -------------------------------------------------------------
    // Global Drag & Drop Prevention
    // -------------------------------------------------------------
    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
        window.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
        document.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    // -------------------------------------------------------------
    // Tab Navigation
    // -------------------------------------------------------------
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
        });
    });

    // -------------------------------------------------------------
    // File Upload & Drag & Drop Handling
    // -------------------------------------------------------------
    fileInput.addEventListener("click", () => {
        fileInput.value = "";
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    [dropZone, fileInput].forEach(elem => {
        if (!elem) return;
        ["dragenter", "dragover"].forEach(eventName => {
            elem.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add("dragover");
            }, false);
        });

        elem.addEventListener("dragleave", (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        }, false);

        elem.addEventListener("drop", (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
            const files = (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0)
                ? e.dataTransfer.files
                : (e.target && e.target.files && e.target.files.length > 0 ? e.target.files : null);
            if (files && files.length > 0) {
                try {
                    fileInput.files = files;
                } catch (_) {}
                handleFile(files[0]);
            } else if (e.dataTransfer) {
                const textData = e.dataTransfer.getData("text/plain") || e.dataTransfer.getData("text/uri-list");
                if (textData && textData.trim()) {
                    clearFileSelection();
                    inputText.value = textData.trim();
                    if (textData.trim().startsWith("http://") || textData.trim().startsWith("https://")) {
                        formatSelect.value = "auto";
                    } else if (textData.includes("\t")) {
                        formatSelect.value = "tsv";
                    } else if (textData.includes(",")) {
                        formatSelect.value = "csv";
                    }
                    if (typeof window !== "undefined" && window.location && analyzeBtn && typeof analyzeBtn.click === "function") {
                        analyzeBtn.click();
                    }
                }
            }
        }, false);
    });

    function formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const chunkSize = 0x8000; // 32KB chunking to avoid max call stack limits
        for (let i = 0; i < bytes.length; i += chunkSize) {
            binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
        }
        return window.btoa(binary);
    }

    function clearFileSelection() {
        currentFile = null;
        uploadedBase64 = null;
        isBinaryFile = false;
        fileInput.value = "";
        fileNameDisplay.textContent = "";
        fileNameDisplay.classList.add("hidden");
        if (fileMetadataPanel) fileMetadataPanel.classList.add("hidden");
        inputText.readOnly = false;
        if (sheetSelect) {
            sheetSelect.innerHTML = "";
            sheetSelect.classList.add("hidden");
        }
        if (sheetNameInput) {
            sheetNameInput.classList.remove("hidden");
            sheetNameInput.value = "";
        }
    }

    async function fetchWorkbookSheets(content, format, filename) {
        if (!sheetSelect || !sheetNameInput) return;
        try {
            const resp = await fetch("/api/sheets", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content: content,
                    format: format || "auto",
                    filename: filename,
                    encoding: "base64"
                })
            });
            if (!resp.ok) return;
            const data = await resp.json();
            if (data.success && Array.isArray(data.sheets) && data.sheets.length > 0) {
                sheetSelect.innerHTML = "";
                data.sheets.forEach(s => {
                    const opt = document.createElement("option");
                    opt.value = s;
                    opt.textContent = s;
                    sheetSelect.appendChild(opt);
                });
                const active = data.active_sheet || data.sheets[0];
                sheetSelect.value = active;
                sheetNameInput.value = active;
                sheetSelect.classList.remove("hidden");
                if (sheetLabel) sheetLabel.classList.remove("hidden");
                sheetSelect.onchange = () => {
                    sheetNameInput.value = sheetSelect.value;
                    if (typeof window !== "undefined" && window.location && analyzeBtn && typeof analyzeBtn.click === "function") {
                        analyzeBtn.click();
                    }
                };
            }
        } catch (_) {
            // Keep fallback manual sheetNameInput
        }
    }

    if (metaClearBtn) {
        metaClearBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            clearFileSelection();
            inputText.value = "";
        });
    }

    if (inputText) {
        inputText.addEventListener("paste", () => {
            setTimeout(() => {
                const val = inputText.value.trim();
                if (val.startsWith("https://docs.google.com/spreadsheets/")) {
                    formatSelect.value = "auto";
                    if (typeof window !== "undefined" && window.location && analyzeBtn && typeof analyzeBtn.click === "function") {
                        analyzeBtn.click();
                    }
                }
            }, 50);
        });
    }

    function handleFile(file) {
        if (!file) return;

        // Check 50MB maximum file size limit
        const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
        if (file.size > MAX_FILE_SIZE) {
            const sizeStr = formatFileSize(file.size);
            const errSummary = currentLang === "vi"
                ? `Tệp "${file.name}" (${sizeStr}) vượt quá giới hạn 50MB tối đa. Vui lòng chọn tệp nhỏ hơn.`
                : `File "${file.name}" (${sizeStr}) exceeds the maximum 50MB limit. Please choose a smaller file.`;
            showError(errSummary, 413, {
                filename: file.name,
                file_size_bytes: file.size,
                limit_bytes: MAX_FILE_SIZE,
                exception_type: "PayloadTooLarge",
                exception_message: `File size exceeds 50MB maximum threshold.`
            }, 1);
            clearFileSelection();
            return;
        }

        currentFile = file;

        const ext = file.name.split(".").pop().toLowerCase();
        if (ext === "tsv") {
            formatSelect.value = "tsv";
        } else if (ext === "csv") {
            formatSelect.value = "csv";
        } else if (ext === "json") {
            formatSelect.value = "json";
        } else if (["xlsx", "xlsm", "xltx", "xltm"].includes(ext)) {
            formatSelect.value = "xlsx";
        } else if (ext === "xls") {
            formatSelect.value = "xls";
        } else if (ext === "ods") {
            formatSelect.value = "ods";
        }

        const sizeStr = formatFileSize(file.size);
        fileNameDisplay.innerHTML = `📄 <strong>Selected File:</strong> ${escapeHtml(file.name)} (${sizeStr}) [${ext.toUpperCase()}] <button type="button" id="clear-file-btn" class="alert-close" style="font-size:1.1rem;margin-left:0.5rem;vertical-align:middle;" title="Remove selected file">&times;</button>`;
        fileNameDisplay.classList.remove("hidden");

        const clearBtnElem = document.getElementById("clear-file-btn");
        if (clearBtnElem) {
            clearBtnElem.addEventListener("click", (e) => {
                e.stopPropagation();
                clearFileSelection();
                inputText.value = "";
            });
        }

        isBinaryFile = ["xlsx", "xls", "ods", "xlsm", "xltx", "xltm"].includes(ext);
        
        // Update Metadata Panel
        if (fileMetadataPanel) {
            if (metaFilename) metaFilename.textContent = file.name;
            if (metaSize) metaSize.textContent = `${sizeStr} (${file.size.toLocaleString()} bytes)`;
            if (metaFormat) metaFormat.textContent = ext.toUpperCase() + (isBinaryFile ? " (Binary Workbook)" : " (Text Matrix)");
            if (metaMode) metaMode.textContent = isBinaryFile ? "Base64 Binary Upload" : "UTF-8 Text Payload";
            fileMetadataPanel.classList.remove("hidden");
        }

        if (isBinaryFile) {
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    if (typeof e.target.result === "string") {
                        uploadedBase64 = e.target.result;
                    } else {
                        uploadedBase64 = arrayBufferToBase64(e.target.result);
                    }
                    inputText.value = `[Binary Workbook Loaded: ${file.name} (${sizeStr})]`;
                    inputText.readOnly = true; // Prevent accidental editing of binary tag
                    hideError();
                    if (typeof window !== "undefined" && window.location && typeof fetch === "function") {
                        await fetchWorkbookSheets(uploadedBase64, formatSelect.value, file.name);
                    }
                    if (typeof window !== "undefined" && window.location && analyzeBtn && typeof analyzeBtn.click === "function") {
                        analyzeBtn.click();
                    }
                } catch (err) {
                    showError("Failed to encode binary file into Base64 format.", 400, {
                        filename: file.name,
                        format: ext,
                        sheet_name: sheetNameInput.value || "Default",
                        exception_type: "EncodingError",
                        exception_message: err.message || String(err)
                    }, 1);
                }
            };
            reader.onerror = () => {
                showError("Failed to read selected binary spreadsheet file.", 400, {
                    filename: file.name,
                    format: ext,
                    sheet_name: sheetNameInput.value || "Default",
                    exception_type: "FileReaderError",
                    exception_message: "FileReader failed to convert binary file."
                }, 1);
            };
            if (typeof reader.readAsDataURL === "function") {
                reader.readAsDataURL(file);
            } else {
                reader.readAsArrayBuffer(file);
            }
        } else {
            uploadedBase64 = null;
            inputText.readOnly = false;
            const reader = new FileReader();
            reader.onload = (e) => {
                inputText.value = e.target.result;
                hideError();
                if (typeof window !== "undefined" && window.location && analyzeBtn && typeof analyzeBtn.click === "function") {
                    analyzeBtn.click();
                }
            };
            reader.onerror = () => {
                showError("Failed to read selected text file.", 400, {
                    filename: file.name,
                    format: ext,
                    sheet_name: sheetNameInput.value || "Default",
                    exception_type: "FileReaderError",
                    exception_message: "FileReader failed to read text file."
                }, 1);
            };
            reader.readAsText(file, "utf-8");
        }
    }


    // -------------------------------------------------------------
    // Staged Progress UI Controller
    // -------------------------------------------------------------
    function updateProgressStep(stepNum, status, customMessage = null) {
        // stepNum: 1..6
        // status: 'active', 'completed', 'failed', 'pending'
        const pct = Math.min(100, Math.round(((stepNum - 1) / 5) * 100));
        if (progressBarFill) {
            progressBarFill.style.width = `${status === 'completed' && stepNum === 6 ? 100 : pct}%`;
        }

        const stepName = STEP_NAMES[stepNum] || "Processing";
        if (progressStepText) {
            progressStepText.textContent = customMessage || `Step ${stepNum} of 6: ${stepName}...`;
        }

        for (let i = 1; i <= 6; i++) {
            const marker = document.getElementById(`step-marker-${i}`);
            if (!marker) continue;
            const badge = marker.querySelector(".step-badge");

            if (i < stepNum) {
                marker.className = "step-item completed";
                if (badge) { badge.textContent = "Done"; badge.className = "step-badge completed"; }
            } else if (i === stepNum) {
                if (status === "failed") {
                    marker.className = "step-item failed";
                    if (badge) { badge.textContent = "Failed"; badge.className = "step-badge failed"; }
                } else if (status === "completed") {
                    marker.className = "step-item completed";
                    if (badge) { badge.textContent = "Done"; badge.className = "step-badge completed"; }
                } else {
                    marker.className = "step-item active";
                    if (badge) { badge.textContent = "In Progress"; badge.className = "step-badge active"; }
                }
            } else {
                marker.className = "step-item";
                if (badge) { badge.textContent = "Pending"; badge.className = "step-badge pending"; }
            }
        }
    }

    function showLoadingOverlay() {
        loadingOverlay.classList.remove("hidden");
        analyzeBtn.disabled = true;
        clearBtn.disabled = true;
    }

    function hideLoadingOverlay() {
        loadingOverlay.classList.add("hidden");
        analyzeBtn.disabled = false;
        clearBtn.disabled = false;
    }

    if (cancelAnalyzeBtn) {
        cancelAnalyzeBtn.addEventListener("click", () => {
            if (currentAbortController) {
                currentAbortController.abort();
                currentAbortController = null;
            }
        });
    }

    // -------------------------------------------------------------
    // Analyze Action
    // -------------------------------------------------------------
    analyzeBtn.addEventListener("click", async () => {
        let contentToSend = inputText.value.trim();
        let encodingToSend = "text";
        let filenameToSend = currentFile ? currentFile.name : null;

        // Step 1: Reading file
        showLoadingOverlay();
        updateProgressStep(1, "active", "Step 1 of 6: Verifying file payload...");

        if (currentFile && isBinaryFile) {
            if (!uploadedBase64) {
                hideLoadingOverlay();
                showError("Binary file is still being processed. Please try again in a moment.", 400, {
                    filename: filenameToSend || "N/A",
                    format: formatSelect.value,
                    sheet_name: sheetNameInput.value.trim() || "Default",
                    exception_type: "StateError",
                    exception_message: "Base64 payload not ready."
                }, 1);
                return;
            }
            contentToSend = uploadedBase64;
            encodingToSend = "base64";
        }

        if (!contentToSend) {
            hideLoadingOverlay();
            showError("Please paste spreadsheet matrix text or upload a file before analyzing.", 400, {
                filename: filenameToSend || "N/A",
                format: formatSelect.value,
                sheet_name: sheetNameInput.value.trim() || "Default",
                exception_type: "ValueError",
                exception_message: "Input spreadsheet content is empty."
            }, 1);
            return;
        }

        updateProgressStep(1, "completed");

        // Step 2: Preparing upload
        updateProgressStep(2, "active", "Step 2 of 6: Preparing JSON request payload...");

        currentRequestId = `req-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
        currentAbortController = new AbortController();
        const timeoutId = setTimeout(() => {
            if (currentAbortController) {
                currentAbortController.abort("TIMEOUT");
            }
        }, 30000); // 30-second client timeout

        let payload;
        try {
            payload = {
                request_id: currentRequestId,
                filename: filenameToSend,
                content: contentToSend,
                format: formatSelect.value,
                encoding: encodingToSend,
                sheet_name: sheetNameInput.value.trim() || null
            };
            updateProgressStep(2, "completed");
        } catch (err) {
            clearTimeout(timeoutId);
            hideLoadingOverlay();
            updateProgressStep(2, "failed");
            showError("Failed to construct request payload.", 400, {
                filename: filenameToSend || "N/A",
                format: formatSelect.value,
                sheet_name: sheetNameInput.value.trim() || "Default",
                exception_type: err.name || "PayloadError",
                exception_message: err.message || String(err)
            }, 2);
            return;
        }

        // Step 3: Uploading payload
        updateProgressStep(3, "active", "Step 3 of 6: Transmitting payload to server...");
        let response;
        try {
            response = await fetch("/api/parse", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Request-ID": currentRequestId
                },
                body: JSON.stringify(payload),
                signal: currentAbortController.signal
            });
            updateProgressStep(3, "completed");
        } catch (err) {
            clearTimeout(timeoutId);
            hideLoadingOverlay();
            updateProgressStep(3, "failed");
            if (err.name === "AbortError") {
                const isTimeout = currentAbortController && currentAbortController.signal.reason === "TIMEOUT";
                const msg = isTimeout ? "Analysis request timed out after 30 seconds." : "Analysis request was canceled by user.";
                showError(msg, 408, {
                    filename: filenameToSend || "N/A",
                    format: formatSelect.value,
                    sheet_name: sheetNameInput.value.trim() || "Default",
                    exception_type: isTimeout ? "TimeoutError" : "AbortError",
                    exception_message: msg
                }, 3);
            } else {
                showError(`Network upload error: ${err.message || String(err)}`, 0, {
                    filename: filenameToSend || "N/A",
                    format: formatSelect.value,
                    sheet_name: sheetNameInput.value.trim() || "Default",
                    exception_type: err.name || "FetchError",
                    exception_message: err.message || String(err)
                }, 3);
            }
            return;
        } finally {
            clearTimeout(timeoutId);
        }

        // Step 4: Parsing workbook (Server Processing)
        updateProgressStep(4, "active", "Step 4 of 6: Server parsing matrix & detecting hierarchy...");
        let data;
        try {
            data = await response.json();
        } catch (err) {
            hideLoadingOverlay();
            updateProgressStep(4, "failed");
            showError("Failed to parse JSON response from server.", response.status, {
                filename: filenameToSend || "N/A",
                format: formatSelect.value,
                sheet_name: sheetNameInput.value.trim() || "Default",
                exception_type: "JSONResponseError",
                exception_message: `Server returned non-JSON body (HTTP ${response.status})`
            }, 4);
            return;
        }

        if (!response.ok || !data.success) {
            hideLoadingOverlay();
            updateProgressStep(4, "failed");
            const errDetails = data.details || {
                filename: filenameToSend || "N/A",
                format: formatSelect.value,
                sheet_name: sheetNameInput.value.trim() || "Default / Active Sheet",
                exception_type: "HTTPError",
                exception_message: data.error || `HTTP ${response.status}`
            };
            showError(
                data.error || `Server error (${response.status})`,
                data.status_code || response.status,
                errDetails,
                4,
                data.request_id || currentRequestId,
                data.timestamp
            );
            return;
        }

        updateProgressStep(4, "completed");

        // Step 5: Building result
        updateProgressStep(5, "active", "Step 5 of 6: Rendering preview & formatting JSON tree...");
        try {
            currentResult = data.result;
            currentPreview = data.preview;
            currentMarkdown = data.markdown || "";
            renderResults(data.result, data.preview, data.metadata_summary, data.markdown || "");
            updateProgressStep(5, "completed");
        } catch (err) {
            hideLoadingOverlay();
            updateProgressStep(5, "failed");
            showError("Failed to render parse results.", 500, {
                filename: filenameToSend || "N/A",
                format: formatSelect.value,
                sheet_name: sheetNameInput.value.trim() || "Default",
                exception_type: err.name || "RenderError",
                exception_message: err.message || String(err)
            }, 5);
            return;
        }

        // Step 6: Completed
        updateProgressStep(6, "completed", "Step 6 of 6: Complete!");
        setTimeout(() => {
            hideLoadingOverlay();
        }, 300);
    });

    // -------------------------------------------------------------
    // Render Results
    // -------------------------------------------------------------
    function renderResults(result, previewText, summary, markdownText) {
        // Enable export buttons
        copyJsonBtn.disabled = false;
        downloadJsonBtn.disabled = false;
        if (copyMdBtn) copyMdBtn.disabled = false;
        if (downloadMdBtn) downloadMdBtn.disabled = false;

        // 1. Render Preview Text
        previewOutput.textContent = previewText || "No preview available.";

        // 2. Render JSON Output
        jsonOutput.textContent = JSON.stringify(result, null, 2);

        // 3. Render Markdown Output
        currentMarkdown = markdownText || "";
        if (markdownOutput) {
            if (currentMarkdown) {
                markdownOutput.textContent = currentMarkdown;
                if (markdownEmpty) markdownEmpty.classList.add("hidden");
                if (markdownContent) markdownContent.classList.remove("hidden");
            } else {
                if (markdownEmpty) markdownEmpty.classList.remove("hidden");
                if (markdownContent) markdownContent.classList.add("hidden");
            }
        }

        // 4. Render Metrics
        summaryMetrics.classList.remove("hidden");
        const meta = result.metadata || {};
        const validation = meta.validation || {};
        const is_valid = validation.is_valid !== undefined ? validation.is_valid : true;

        if (is_valid) {
            metricStatus.textContent = "VALID";
            metricStatus.className = "metric-value badge badge-success";
        } else {
            const errs = validation.error_count || 0;
            metricStatus.textContent = `INVALID (${errs} Err)`;
            metricStatus.className = "metric-value badge badge-danger";
        }

        if (metricFormat) {
            metricFormat.textContent = (meta.source_format || summary?.source_format || "AUTO").toUpperCase();
        }
        if (metricSheet) {
            metricSheet.textContent = meta.sheet_name || summary?.sheet_name || "Default";
        }
        if (metricDims) {
            const gridDims = meta.grid_dimensions || (summary?.num_rows !== undefined ? { rows: summary.num_rows, cols: summary.num_cols } : null);
            if (gridDims) {
                metricDims.textContent = `${gridDims.rows} x ${gridDims.cols}`;
            } else {
                metricDims.textContent = "N/A";
            }
        }

        const tables = result.tables || [];
        const orphans = result.orphan_tables || [];
        const warnings = meta.warnings || [];
        const unclassified = result.unclassified_rows || [];

        metricTables.textContent = tables.length;
        metricOrphans.textContent = orphans.length;
        metricWarnings.textContent = warnings.length;
        metricUnclassified.textContent = unclassified.length;

        // 5. Render Details Tab
        detailsEmpty.classList.add("hidden");
        detailsContent.classList.remove("hidden");

        // Render Tables
        tablesList.innerHTML = "";
        if (tables.length === 0) {
            tablesList.innerHTML = "<p class='text-muted'>No hierarchical tables detected.</p>";
        } else {
            tables.forEach(t => {
                tablesList.appendChild(createTableCard(t));
            });
        }

        // Render Orphans
        if (orphans.length > 0) {
            orphansSection.classList.remove("hidden");
            orphansList.innerHTML = "";
            orphans.forEach(ot => {
                orphansList.appendChild(createTableCard(ot, true));
            });
        } else {
            orphansSection.classList.add("hidden");
        }

        // Render Global Warnings
        if (warnings.length > 0) {
            warningsSection.classList.remove("hidden");
            warningsList.innerHTML = "";
            warnings.forEach(w => {
                const chip = document.createElement("span");
                chip.className = "warning-chip";
                chip.textContent = w;
                warningsList.appendChild(chip);
            });
        } else {
            warningsSection.classList.add("hidden");
        }

        // Render Unclassified Rows
        if (unclassified.length > 0) {
            unclassifiedSection.classList.remove("hidden");
            unclassifiedList.innerHTML = renderUnclassifiedTable(unclassified);
        } else {
            unclassifiedSection.classList.add("hidden");
        }

        // 6. Render Table Catalog Registry Tab
        renderCatalogTable(tables, orphans);
    }

    let allCatalogRows = [];

    function renderCatalogTable(tables, orphans) {
        if (!catalogTableBody) return;
        
        allCatalogRows = [];
        let index = 1;

        function addTableToCatalog(t, isOrphan = false) {
            const isSec = t.node_type === "section" || ((t.records || []).length === 0 && (t.children || []).length > 0);
            allCatalogRows.push({
                idx: index++,
                table_id: t.table_id || "",
                title: t.title || "<Untitled>",
                level: t.level !== undefined ? t.level : (isOrphan ? "Orphan" : 0),
                parent_id: t.parent_id || (isOrphan ? "None (Orphan)" : "Root"),
                start_row: (t.data_range?.start_row || 0) + 1,
                start_col: (t.data_range?.start_col || 0) + 1,
                end_row: (t.data_range?.end_row || 0) + 1,
                end_col: (t.data_range?.end_col || 0) + 1,
                records_count: (t.records || []).length,
                children_count: (t.children || []).length,
                cols_count: (t.columns || []).length,
                confidence: isSec ? 1.0 : (t.confidence !== undefined ? t.confidence : 1.0),
                is_orphan: isOrphan && !isSec,
                is_section: isSec
            });
        }

        tables.forEach(t => addTableToCatalog(t, false));
        orphans.forEach(ot => addTableToCatalog(ot, true));

        if (allCatalogRows.length === 0) {
            if (catalogEmpty) catalogEmpty.classList.remove("hidden");
            if (catalogContent) catalogContent.classList.add("hidden");
            return;
        }

        if (catalogEmpty) catalogEmpty.classList.add("hidden");
        if (catalogContent) catalogContent.classList.remove("hidden");
        updateCatalogView();
    }

    function updateCatalogView() {
        if (!catalogTableBody) return;
        const query = (catalogSearchInput?.value || "").trim().toLowerCase();
        const filter = catalogLevelFilter?.value || "all";

        const filtered = allCatalogRows.filter(row => {
            if (filter === "sections" && !row.is_section) return false;
            if (filter === "root" && (row.level > 1 || row.is_orphan || row.is_section)) return false;
            if (filter === "sub" && (row.level <= 1 || row.is_orphan || row.is_section)) return false;
            if (filter === "orphans" && (!row.is_orphan || row.is_section)) return false;

            if (query) {
                const matchId = row.table_id.toLowerCase().includes(query);
                const matchTitle = row.title.toLowerCase().includes(query);
                const matchParent = String(row.parent_id).toLowerCase().includes(query);
                const matchRange = `r${row.start_row}c${row.start_col}`.includes(query);
                return matchId || matchTitle || matchParent || matchRange;
            }
            return true;
        });

        if (catalogCountBadge) {
            catalogCountBadge.textContent = `${filtered.length} of ${allCatalogRows.length} tables`;
        }

        if (filtered.length === 0) {
            catalogTableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:1.5rem; color:var(--text-muted);">No tables match the search/filter criteria.</td></tr>`;
            return;
        }

        catalogTableBody.innerHTML = filtered.map(row => {
            const rangeStr = `R${row.start_row}C${row.start_col} : R${row.end_row}C${row.end_col}`;
            const confPct = Math.round(row.confidence * 100);
            const confBadgeClass = confPct >= 90 ? "badge-success" : (confPct >= 70 ? "badge-version" : "badge-danger");
            
            let levelBadge = "";
            if (row.is_section) {
                levelBadge = `<span class="badge badge-section">📁 Section (L${row.level})</span>`;
            } else if (row.is_orphan) {
                levelBadge = `<span class="badge badge-danger">Orphan</span>`;
            } else if (row.level <= 1) {
                levelBadge = `<span class="badge badge-success">Level ${row.level} (Root)</span>`;
            } else {
                levelBadge = `<span class="badge badge-version">Level ${row.level}</span>`;
            }
            
            const indentPrefix = row.level > 1 ? "&nbsp;&nbsp;".repeat(row.level - 1) + "↳ " : "";
            const titleDisplay = row.is_section 
                ? `<strong>📁 ${escapeHtml(row.title)}</strong> <em style="font-size:0.75rem; color:var(--text-muted);">(Chuyên mục)</em>`
                : `<span style="font-weight:${row.level <= 1 ? '600' : 'normal'};">${escapeHtml(row.title)}</span>`;

            const recordsDisplay = row.is_section
                ? `<span class="badge badge-section">📁 ${row.children_count} sub-tables</span>`
                : `<span class="badge ${row.records_count > 0 ? 'badge-version' : 'badge-outline'}">${row.records_count} rows</span>`;

            return `
                <tr class="${row.is_section ? 'catalog-section-row' : ''}">
                    <td style="color:var(--text-muted); font-size:0.75rem;">${row.idx}</td>
                    <td><strong style="font-family:monospace; color:${row.is_section ? '#7e22ce' : 'var(--primary)'};">${escapeHtml(row.table_id)}</strong></td>
                    <td>
                        <div class="catalog-title-cell">
                            <span class="catalog-tree-indent">${indentPrefix}</span>
                            ${titleDisplay}
                        </div>
                    </td>
                    <td>${levelBadge}</td>
                    <td style="font-family:monospace; font-size:0.75rem; color:var(--text-secondary);">${escapeHtml(row.parent_id)}</td>
                    <td style="font-family:monospace; font-size:0.75rem;">${rangeStr}</td>
                    <td>${recordsDisplay}</td>
                    <td>${row.is_section ? "—" : row.cols_count}</td>
                    <td><span class="badge ${confBadgeClass}">${confPct}%</span></td>
                </tr>
            `;
        }).join("");
    }


    function createTableCard(table, isOrphan = false) {
        const card = document.createElement("div");
        const isSection = table.node_type === "section" || ((table.records || []).length === 0 && (table.children || []).length > 0);
        card.className = `table-card ${isSection ? 'section-card' : ''}`;

        const title = escapeHtml(table.title || "<Untitled Table>");
        const tid = escapeHtml(table.table_id || "");
        const level = table.level !== undefined ? table.level : 0;
        const parentId = table.parent_id ? escapeHtml(table.parent_id) : "None (Root)";
        const conf = isSection ? "1.00" : (table.confidence !== undefined ? table.confidence : 1.0).toFixed(2);

        const dr = table.data_range || {};
        const rangeStr = `R${(dr.start_row || 0) + 1}C${(dr.start_col || 0) + 1} : R${(dr.end_row || 0) + 1}C${(dr.end_col || 0) + 1}`;
        const headerRow1 = (table.header_row !== undefined ? table.header_row : 0) + 1;
        const records = table.records || [];
        const recCount = records.length;
        const cols = table.columns || [];
        const children = table.children || [];

        let colsHtml = cols.map(c => `<span class="chip">${escapeHtml(c)}</span>`).join("");

        let warnsHtml = "";
        if (!isSection && table.warnings && table.warnings.length > 0) {
            warnsHtml = `<div class="warnings-chips" style="margin-top: 0.25rem;">` +
                table.warnings.map(w => `<span class="warning-chip">${escapeHtml(w)}</span>`).join("") +
                `</div>`;
        }

        if (isSection) {
            // Render specialized Section Header Card
            card.innerHTML = `
                <div class="table-card-header">
                    <span class="table-title" style="color:#6b21a8;">📁 [${tid}] "${title}"</span>
                    <div class="table-meta-tags">
                        <span class="badge badge-section">📁 Section Container (Level ${level})</span>
                    </div>
                </div>
                <div class="table-meta-grid" style="margin-top:0.4rem;">
                    <div><strong>Type:</strong> Category Banner / Chuyên mục lớn</div>
                    <div><strong>Parent:</strong> ${parentId}</div>
                    <div><strong>Range:</strong> ${rangeStr}</div>
                    <div><strong>Sub-tables:</strong> ${children.length} bảng dữ liệu con</div>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.78rem; color: #6b21a8; font-style: italic;">
                    💡 Dòng trình bày định vị phân nhóm — chứa các bảng con: ${children.map(c => `<code style="background:#f3e8ff; padding:0.1rem 0.3rem; border-radius:3px;">${escapeHtml(c)}</code>`).join(", ")}
                </div>
            `;
            return card;
        }

        // Standard Table Card records table HTML
        let recordsHtml = "";
        if (cols.length > 0 && recCount > 0) {
            let thead = `<tr>` + cols.map(c => `<th>${escapeHtml(c)}</th>`).join("") + `</tr>`;
            let tbody = records.map(rec => {
                const cells = cols.map(c => {
                    const val = rec[c];
                    return `<td>${escapeHtml(val !== null && val !== undefined ? String(val) : "")}</td>`;
                }).join("");
                return `<tr>${cells}</tr>`;
            }).join("");
            recordsHtml = `
                <details class="records-details" style="margin-top:0.6rem;">
                    <summary style="cursor:pointer; font-size:0.78rem; font-weight:600; color:var(--text-muted); user-select:none;">
                        📋 View ${recCount} record${recCount !== 1 ? "s" : ""}
                    </summary>
                    <div style="overflow-x:auto; margin-top:0.4rem;">
                        <table class="records-inline-table">
                            <thead>${thead}</thead>
                            <tbody>${tbody}</tbody>
                        </table>
                    </div>
                </details>`;
        } else if (cols.length > 0 && recCount === 0) {
            recordsHtml = `<p style="font-size:0.78rem; color:var(--text-muted); margin-top:0.4rem; font-style:italic;">No records found in this table.</p>`;
        }

        card.innerHTML = `
            <div class="table-card-header">
                <span class="table-title">[${tid}] "${title}"</span>
                <div class="table-meta-tags">
                    <span class="badge ${isOrphan ? 'badge-danger' : 'badge-version'}">Level ${level}</span>
                </div>
            </div>
            <div class="table-meta-grid">
                <div><strong>Parent:</strong> ${parentId}</div>
                <div><strong>Range:</strong> ${rangeStr}</div>
                <div><strong>Anchor Col:</strong> ${(table.anchor_column || 0) + 1}</div>
                <div><strong>Header Row:</strong> ${headerRow1}</div>
                <div><strong>Records:</strong> ${recCount}</div>
                <div><strong>Confidence:</strong> ${conf}</div>
            </div>
            <div>
                <strong style="font-size: 0.75rem; color: var(--text-muted);">Columns (${cols.length}):</strong>
                <div class="columns-chips" style="margin-top: 0.25rem;">${colsHtml || '<em>None</em>'}</div>
            </div>
            ${warnsHtml}
            ${recordsHtml}
        `;

        return card;
    }

    function renderUnclassifiedTable(rows) {
        let html = `
            <table class="unclassified-table">
                <thead>
                    <tr>
                        <th style="width: 80px;">Row Index</th>
                        <th>Unclassified Cells & Values</th>
                    </tr>
                </thead>
                <tbody>
        `;

        rows.forEach(r => {
            const rIdx = r.row !== undefined ? r.row : "?";
            const cells = (r.cells || []).map(c => `[Col ${c.col}: "${escapeHtml(c.value)}"]`).join(", ");
            html += `
                <tr>
                    <td>Row ${rIdx}</td>
                    <td>${cells}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;
        return html;
    }

    // -------------------------------------------------------------
    // Clear Action
    // -------------------------------------------------------------
    clearBtn.addEventListener("click", () => {
        inputText.value = "";
        sheetNameInput.value = "";
        formatSelect.value = "auto";
        clearFileSelection();

        currentResult = null;
        currentPreview = "";

        copyJsonBtn.disabled = true;
        downloadJsonBtn.disabled = true;
        if (copyMdBtn) copyMdBtn.disabled = true;
        if (downloadMdBtn) downloadMdBtn.disabled = true;

        currentMarkdown = "";
        previewOutput.textContent = 'No dataset analyzed yet. Paste spreadsheet text or upload a file and click "Analyze Sheet".';
        jsonOutput.textContent = '{\n  "info": "JSON contract output will appear here after parsing."\n}';
        if (markdownOutput) markdownOutput.textContent = "";
        if (markdownEmpty) markdownEmpty.classList.remove("hidden");
        if (markdownContent) markdownContent.classList.add("hidden");
        
        // Reset Catalog Tab
        allCatalogRows = [];
        if (catalogTableBody) catalogTableBody.innerHTML = "";
        if (catalogEmpty) catalogEmpty.classList.remove("hidden");
        if (catalogContent) catalogContent.classList.add("hidden");
        if (catalogSearchInput) catalogSearchInput.value = "";
        if (catalogLevelFilter) catalogLevelFilter.value = "all";
        if (catalogCountBadge) catalogCountBadge.textContent = "0 tables";

        summaryMetrics.classList.add("hidden");

        detailsContent.classList.add("hidden");
        detailsEmpty.classList.remove("hidden");

        hideError();
    });

    // Catalog Filter & Search Listeners
    if (catalogSearchInput) {
        catalogSearchInput.addEventListener("input", updateCatalogView);
    }
    if (catalogLevelFilter) {
        catalogLevelFilter.addEventListener("change", updateCatalogView);
    }

    // -------------------------------------------------------------
    // Copy JSON Action
    // -------------------------------------------------------------
    copyJsonBtn.addEventListener("click", () => {
        if (!currentResult) return;
        const textToCopy = JSON.stringify(currentResult, null, 2);
        
        copyToClipboard(textToCopy).then(() => {
            const originalText = copyJsonBtn.innerHTML;
            copyJsonBtn.innerHTML = "<span>✅ Copied!</span>";
            setTimeout(() => {
                copyJsonBtn.innerHTML = originalText;
            }, 2000);
        }).catch(() => {
            showError("Failed to copy JSON to clipboard.");
        });
    });

    // -------------------------------------------------------------
    // Download JSON Action
    // -------------------------------------------------------------
    downloadJsonBtn.addEventListener("click", () => {
        if (!currentResult) return;
        const jsonStr = JSON.stringify(currentResult, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "spatial_sheet_parsed.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // -------------------------------------------------------------
    // Copy Markdown Action
    // -------------------------------------------------------------
    if (copyMdBtn) {
        copyMdBtn.addEventListener("click", () => {
            if (!currentMarkdown) return;
            copyToClipboard(currentMarkdown).then(() => {
                const originalText = copyMdBtn.innerHTML;
                copyMdBtn.innerHTML = "<span>✅ Copied!</span>";
                setTimeout(() => {
                    copyMdBtn.innerHTML = originalText;
                }, 2000);
            }).catch(() => {
                showError("Failed to copy Markdown to clipboard.");
            });
        });
    }

    // -------------------------------------------------------------
    // Download Markdown Action
    // -------------------------------------------------------------
    if (downloadMdBtn) {
        downloadMdBtn.addEventListener("click", () => {
            if (!currentMarkdown) return;
            const blob = new Blob([currentMarkdown], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "spatial_sheet_parsed.md";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    // -------------------------------------------------------------
    // Copy Error Button Action
    // -------------------------------------------------------------
    if (copyErrorBtn) {
        copyErrorBtn.addEventListener("click", () => {
            if (!lastErrorDetails) return;
            copyToClipboard(lastErrorDetails).then(() => {
                const originalHtml = copyErrorBtn.innerHTML;
                copyErrorBtn.innerHTML = "<span>✅ Error Copied!</span>";
                setTimeout(() => {
                    copyErrorBtn.innerHTML = originalHtml;
                }, 2000);
            }).catch(() => {
                alert("Failed to copy error details to clipboard.");
            });
        });
    }

    // -------------------------------------------------------------
    // Error Reporting Helper Functions
    // -------------------------------------------------------------
    function showError(msg, statusCode = 400, details = null, failedStep = null, reqId = null, timestamp = null) {
        const ts = timestamp || (new Date()).toISOString();
        const rid = reqId || currentRequestId || `req-${Date.now()}`;
        const statusStr = statusCode ? `${statusCode}` : "Error";
        const stepName = failedStep ? `Step ${failedStep} (${STEP_NAMES[failedStep] || "Processing"})` : "N/A";

        errorMessage.textContent = failedStep ? `[Failed at Step ${failedStep}: ${STEP_NAMES[failedStep]}] ${msg}` : msg;

        let techDetailsText = `=== SPATIAL SHEET PARSER ERROR REPORT ===\n`;
        techDetailsText += `Timestamp       : ${ts}\n`;
        techDetailsText += `Request ID      : ${rid}\n`;
        techDetailsText += `Failed Step     : ${stepName}\n`;
        techDetailsText += `HTTP Status     : ${statusStr}\n`;
        if (details) {
            techDetailsText += `Filename        : ${details.filename || "N/A"}\n`;
            techDetailsText += `Detected Format : ${details.format || "N/A"}\n`;
            techDetailsText += `Sheet Name      : ${details.sheet_name || "N/A"}\n`;
            techDetailsText += `Exception Type  : ${details.exception_type || "N/A"}\n`;
            techDetailsText += `Exception Msg   : ${details.exception_message || details.exception || msg}\n`;
        } else {
            techDetailsText += `Message         : ${msg}\n`;
        }

        lastErrorDetails = techDetailsText;

        if (errorDetailsContent) {
            errorDetailsContent.textContent = techDetailsText;
        }

        errorBanner.classList.remove("hidden");
    }

    function hideError() {
        errorBanner.classList.add("hidden");
    }

    if (closeErrorBtn) {
        closeErrorBtn.addEventListener("click", hideError);
    }

    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }
        return new Promise((resolve, reject) => {
            try {
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.style.position = "fixed";
                textarea.style.left = "-9999px";
                textarea.style.top = "-9999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                const successful = document.execCommand("copy");
                document.body.removeChild(textarea);
                if (successful) resolve();
                else reject(new Error("execCommand copy failed"));
            } catch (e) {
                reject(e);
            }
        });
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
