# Demo Project

智慧型 LINE Bot + 後台 Dashboard + 自動化爬蟲管線 Demo

## 技術特色

### 生產級強化
- **External Call 加入 Circuit Breaker**: 在 LINE API、LLM invoke、Botasaurus crawler 等所有 external call 處加上 circuit breaker 機制（使用自實作簡單版本）。設定：failure_threshold=5、recovery_timeout=30、fallback 機制（當 circuit open 時回傳預設錯誤訊息或 cache 資料）。
- **AI Prompt Validation**: 把目前 YAML 靜態 prompt 改成 Pyd