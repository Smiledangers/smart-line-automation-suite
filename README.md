# 智慧型 LINE Bot + 後台 Dashboard + 自動化爬蟲管線

智慧型自動化平台，結合 LINE Bot、後台管理儀表板與自動化網頁爬蟲管線，提供完整的業務自動化解決方案。

## 🌟 功能特色

- **LINE Bot 整合**：自然語言對話、自動回覆、訊息推播
- **後台 Dashboard**：使用者管理、爬蟲任務監控、AI 對話記錄查看
- **自動化爬蟲管線**：基於 Celery 的分散式任務隊列，支援定時爬蟲與事件觸發爬蟲
- **AI 代理整合**：LangGraph + OpenAI GPT-4，提供智慧對話與決策支援
- **完整測試**：單元測試與整合測試，確保系統穩定性
- **多種部署選項**：Docker Compose、Kubernetes、Helm、Render.com、Railway.app

## 🛠️ 技術棧

- **後端框架**：FastAPI (Python 3.10+)
- **資料庫**：PostgreSQL + SQLAlchemy 2.0
- **快取隊列**：Redis + Celery
- **AI/ML**：LangChain + LangGraph + OpenAI GPT-4
- **LINE Bot**：官方 LINE Messaging API
- **網頁爬蟲**：Botasaurus (反偵測爬蟲框架)
- **異步處理**：Pydantic + Asyncio
- **容器化**：Docker + Docker Compose
- ** orchestration**：Kubernetes + Helm
- **CI/CD**：GitHub Actions
- **測試框架**：Pytest + pytest-asyncio

## 📂 專案結構

```
demo_project/
├── app/                    # 主應用程式
│   ├── api/                # API 路由層
│   ├── core/               # 核心配置 (設定、資料庫、安全)
│   ├── models/             # SQLAlchemy 資料模型
│   ├── schemas/            # Pydantic 資料驗證模式
│   ├── services/           # 業務邏輯服務
│   ├── tasks/              # Celery 異步任務
│   ├── utils/              # 工具函式
│   └── main.py             # FastAPI 應用入口
├── scraper/                # Botasaurus 爬蟲框架
│   ├── spiders/            # 爬蟲蜘蛛定義
│   ├── pipelines/          # 資料處理管線
│   ├── middlewares/        # 爬蟲中間件 (重試等)
│   └── settings.py         # 爬蟲設定
├── ai/                     # AI 代理與決策圖表
│   ├── agents/             # LINE 與爬蟲代理
│   ├── graphs/             # LangGraph 對話與決策圖
│   ├── tools/              # 自訂 LangChain 工具
│   └── prompts/            # YAML 形式的提示詞模板
├── tests/                  # 測試套件
│   ├── unit/               # 單元測試
│   ├── integration/        # 整合測試 (API 端點)
│   ├── conftest.py         # Pytest 配置
│   └── pytest.ini          # Pytest 設定
├── deploy/                 # 部署配置
│   ├── docker/             # Dockerfile 與 docker-compose
│   ├── k8s/                # Kubernetes 生產環境清單
│   ├── helm/               # Helm Chart
│   └── cloud/              # Render.com 與 Railway.app 配置
├── alembic/                # 資料庫遷移腳本
├── requirements/           # Python 依賴清單 (base/dev/prod)
├── scripts/                # 輔助腳本 (建立超級使用者、初始化資料庫等)
├── docs/                   # 技術文件
├── .github/                # GitHub Actions 工作流程
├── .env.example            # 環境變數範本
├── .gitignore              # Git 忽略檔案
├── Dockerfile              # 多階段 Docker 建置
├── docker-compose.yml      # 本地開發環境
├── README.md               # 本檔案
├── pyproject.toml          # 專案設定與依賴
├── Makefile                # 常用開發命令
└── LICENSE                 # MIT 授權
```

## 🚀 快速開始

### 前置需求
- Docker 與 Docker Compose
- Git
- Python 3.10+ (選擇性，若不使用 Docker)
- LINE Developers 帳號 (取得 Channel Access Token 與 Channel Secret)
- OpenAI API 金鑰 (選擇性，用於 AI 功能)

### 本地開發環境

1. **複製儲存庫**
   ```bash
   git clone https://github.com/Smiledangers/demo-project.git
   cd demo-project
   ```

2. **設定環境變數**
   ```bash
   cp .env.example .env
   # 編輯 .env 檔案，填入必要的金鑰：
   # LINE_CHANNEL_ACCESS_TOKEN=
   # LINE_CHANNEL_SECRET=
   # OPENAI_API_KEY=
   # POSTGRES_PASSWORD=
   # REDIS_PASSWORD=
   # SECRET_KEY= (建議使用 32+ 個隨機字元)
   ```

3. **啟動服務**
   ```bash
   # 建置並啟動所有容器
   docker-compose up --build
   
   # 在另一個終端機中執行資料庫遷移
   docker-compose exec backend alembic upgrade head
   ```

4. **訪問應用**
   - API 文件：http://localhost:8000/docs
   - 健康檢查：http://localhost:8000/health
   - Flower (Celery 監控)：http://localhost:5555

## 📚 詳細文件

- [架構設計](./docs/architecture.md)
- [API 參考](./docs/api.md)
- [部署指南](./deployment_instructions.md)
- [開發貢獻指南](./CONTRIBUTING.md)

## 🔐 環境變數說明

參考 `.env.example` 檔案，主要變數包括：

| 變數名稱 | 說明 | 預設值/範例 |
|---------|------|-------------|
| `PROJECT_NAME` | 專案名稱 | 智慧型 LINE Bot + 後台 Dashboard + 自動化爬蟲管線 |
| `POSTGRES_SERVER` | PostgreSQL 主機 | localhost |
| `POSTGRES_USER` | PostgreSQL 使用者 | postgres |
| `POSTGRES_PASSWORD` | PostgreSQL 密碼 | (必填) |
| `POSTGRES_DB` | 資料庫名稱 | demo_bot |
| `REDIS_HOST` | Redis 主機 | localhost |
| `REDIS_PORT` | Redis 埠號 | 6379 |
| `REDIS_PASSWORD` | Redis 密碼 | (選填) |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Channel Access Token | (必填) |
| `LINE_CHANNEL_SECRET` | LINE Bot Channel Secret | (必填) |
| `OPENAI_API_KEY` | OpenAI API 金鑰 | (選填，啟用 AI 功能所需) |
| `SECRET_KEY` | JWT 加密密鑰 | (必填，32+ 隨機字元) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT 過期時間 (分鐘) | 11520 (8 天) |
| `CELERY_BROKER_URL` | Celery 消息代理 | redis://redis:6379/0 |
| `CELERY_RESULT_BACKEND` | Celery 結果後端 | redis://redis:6379/0 |

## 🐳 Docker 部署

### 開發環境
```bash
docker-compose up --build
```

### 生產環境
```bash
# 使用生產設定
docker-compose -f ./deploy/docker/docker-compose.prod.yml up --build
```

## ☸️ Kubernetes 部署

### 前置需求
- Kubernetes 叢集 (v1.20+)
- Helm 3.x
- kubectl

### 部署步驟
```bash
# 添加 Helm 存儲庫
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 安裝依賴服務
helm install postgres bitnami/postgresql --namespace demo-bot --create-namespace
helm install redis bitnami/redis --namespace demo-bot

# 部署主應用
helm upgrade --install demo-bot ./deploy/helm/demo-bot \
  --namespace demo-bot \
  --set image.repository=your-registry/demo-bot \
  --set image.tag=latest \
  --set env.POSTGRES_PASSWORD=your_postgres_password \
  --set env.REDIS_PASSWORD=your_redis_password \
  --set env.LINE_CHANNEL_ACCESS_TOKEN=your_line_token \
  --set env.LINE_CHANNEL_SECRET=your_line_secret \
  --set env.OPENAI_API_KEY=your_openai_key \
  --set env.SECRET_KEY=your_secret_key
```

## ☁️ 雲端平台部署

### Render.com
1. Fork 此倉庫
2. 前往 [Render.com](https://render.com) 新增 Web Service
3. 連接您的 forked 倉庫
4. 設定：
   - 建置命令：`pip install -r requirements/prod.txt`
   - 啟動命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - 添加所有必要的環境變數 (參考 .env.example)
5. 點擊 "Create Web Service"

### Railway.app
1. 前往 [Railway.app](https://railway.app) 並登入
2. 點擊 "New Project" → "Deploy from GitHub"
3. 選擇此倉庫
4. Railway 會自動偵測 Dockerfile
5. 在變數設定中添加所有必要的環境變數
6. 等待部署完成

## 🧪 測試

### 執行單元測試
```bash
# 使用 Docker
docker-compose run --rm backend pytest tests/unit/ -v

# 或直接在本機 (假設已安裝依賴)
pytest tests/unit/ -v
```

### 執行整合測試
```bash
docker-compose run --rm backend pytest tests/integration/ -v
```

### 測試覆蓋率
```bash
docker-compose run --rm backend pytest --cov=app --cov-report=html
```

## 📈 監控與日誌

- **Prometheus + Grafana**：已在 Kubernetes 配置中包含監控設定
- **ELK Stack**：可透過 Docker Compose 擴展日誌收集
- **健康檢查端點**：`GET /health` 返回服務狀態
- **指標端點**：`GET /metrics` (Prometheus 格式)

## 🤝 貢獻指南

歡迎提交 Issue 與 Pull Request！請參考 [CONTRIBUTING.md] 了解貢獻流程。

1. Fork 本倉庫
2. 建立您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權 - 查看 [LICENSE] 檔案取得詳細資訊。

## 🙏 鳴謝

- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryproject.org/)
- [LangChain](https://www.langchain.com/)
- [Botasaurus](https://botasaurus.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)

---

**開發者**：小龍 (Xiǎolóng) - AI 助手  
**最後更新**：2026-04-17  
**版本**：1.0.0