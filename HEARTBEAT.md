# HEARTBEAT.md - Project Iteration

每半小時自動檢查 Smart LINE Bot 專案並迭代改進成更龐大更完美的系統

## 迭代任務（每次心跳執行）

### 1. 專案完整性檢查
- 驗證所有必要檔案是否存在
- 檢查缺少的 models, schemas, endpoints
- 確認 docker-compose.yml 服務完整

### 2. 代碼質量抽查
- 檢查 app/services/ 是否有空方法或 TODO → 填補完整
- 檢查 app/tasks/ 是否完整 → 增加更多 task
- 檢查 models 是否完整 → 增加更多欄位和關聯

### 3. 功能擴展
- 增加新的 API endpoints
- 增加新的 service methods
- 增加新的 Celery tasks
- 增加新的 data models

### 4. 基礎設施擴展
- 增加更多 deployment configs (Terraform, etc)
- 增加更多 tests
- 增加更多 scripts
- 增加更多 docs

### 5. 改進原則
- 每次至少完成 1 個「有感」的改進（不是只有几行代码）
- 目標：讓專案越來越大、越來越完整
- 優先：填補功能 > 擴展功能 > 優化現有
- 改進後自動 commit + push
- 記錄到 memory/YYYY-MM-DD.md

---

## 迭代範例（不是只有這些）
- 新增一個完整的 API endpoint（含 tests）
- 新增一個 Celery task（含 error handling）
- 新增一個 service method（含完整 business logic）
- 新增一個 data model（含 migrations）
- 新增一個 deployment config
- 新增一個 script
- 補完一個空的 skeleton 成為完整功能

---

## 觸發條件
每 30 分鐘執行一次檢查