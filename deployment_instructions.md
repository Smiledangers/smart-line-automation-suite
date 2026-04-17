# 一鍵部署指令

## 開發環境 (Docker Compose)

```bash
# 1. 複製環境變數範例
cp .env.example .env
# 2. 編輯 .env 檔案，填入必要的金鑰（LINE, AI, 等）
# 3. 建置並啟動服務
docker-compose up -d --build
# 4. 執行資料庫遷移
docker-compose exec web alembic upgrade head
# 5. 建立管理員使用者
docker-compose exec web python scripts/create_superuser.py
# 6. 存取應用程式
#   API 文件: http://localhost:8000/docs
#   替代文件: http://localhost:8000/redoc
#   健康檢查: http://localhost:8000/health
```

## 生產環境 (Docker Compose)

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## Kubernetes 部署

```bash
# 應用所有 manifests
kubectl apply -f deploy/k8s/

# 查看部署狀態
kubectl get pods
kubectl get services
```

## 使用 Helm 部署

```bash
helm install demo-bot ./deploy/helm/demo-bot
```

## Render.com 部署

1. 在 Render.com 建立新的 Web Service
2. 連接到您的 GitHub 倉庫
3. 設置構建命令：`docker build -t demo-bot .`
4. 設置啟動命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 添加環境變數（從 .env.example 複製）
6. 自動部署

## Railway.app 部署

1. 在 Railway.app 建立新專案
2. 連接到您的 GitHub 倉庫
3. Railway 會自動檢測 Dockerfile 並構建
4. 添加必要的環境變數
5. 部署

## 本地開發（無 Docker）

```bash
# 1. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安裝依賴
pip install -r requirements/base.txt
pip install -r requirements/dev.txt  # 包含測試和開發工具

# 3. 複製環境變數
cp .env.example .env
# 編輯 .env

# 4. 初始化資料庫
python scripts/init_db.py

# 5. 執行遷移
alembic upgrade head

# 6. 建立管理員使用者
python scripts/create_superuser.py

# 7. 啟動應用程式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 測試指令

```bash
# 執行所有測試
pytest

# 僅執行單元測試
pytest tests/unit/

# 僅執行整合測試
pytest tests/integration/

# 帶覆蓋率報告
pytest --cov=app --cov-report=term-missing

# 特定測試檔案
pytest tests/unit/test_line_service.py
```

## 故障排除

### 資料庫連線問題
- 檢查 `.env` 中的 `DATABASE_URL` 是否正確
- 確保 PostgreSQL 服務正在運行（在 Docker Compose 中是 `db` 服務）
- 檢查網路連線和防火牆設定

### Redis 連線問題
- 檢查 `.env` 中的 `REDIS_URL` 是否正確
- 確保 Redis 服務正在運行（在 Docker Compose 中是 `redis` 服務）

### LINE Webhook 無法連線
- 確保您的伺服器是公開可訪問的（使用 ngrok 或類似工具進行本地測試）
- 在 LINE Developers Console 中設定 Webhook URL 為 `https://your-domain.com/api/v1/line/webhook`
- 檢查 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 是否正確

### AI 服務問題
- 檢查 `.env` 中的 `OPENAI_API_KEY` 是否正確且有足夠的配額
- 如果使用本地 LLM，請確保模型路徑正確並且有足夠的記憶體
- 檢查日誌以了解具體錯誤

### Celery 工作問題
- 檢查 Redis 連線（Celery 使用 Redis 作為經紀人和結果後端）
- 查看工作者日誌：`docker-compose logs worker`
- 確保工作者服務正在運行

## 監控與日誌

### 查看服務日誌
```bash
docker-compose logs -f web        # 主應用程式
docker-compose logs -f worker     # Celery 工作者
docker-compose logs -f db         # PostgreSQL
docker-compose logs -f redis      # Redis
```

### 健康檢查端點
- `GET /health` - 基本存活檢查
- `GET /health/ready` - 就緒檢查（檢查資料庫、Redis 連線等）
- `GET /metrics` - Prometheus 指標（如果啟用）

## 資料庫備份與還原

### 備份
```bash
docker-compose exec db pg_dump -U postgres demo_project > backup.sql
```

### 還原
```bash
cat backup.sql | docker-compose exec -i db psql -U postgres demo_project
```

## 升級專案

```bash
# 拉取最新程式碼
git pull origin main

# 重新建置和重新啟動
docker-compose up -d --build

# 執行新的遷移
docker-compose exec web alembic upgrade head
```