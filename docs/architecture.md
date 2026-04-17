# System Architecture

Overview of the Smart LINE Bot + Dashboard + Scraper Pipeline system architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Clients                                     │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐  ┌───────────────┐  │
│  │ LINE    │  │ Web UI   │  │ Mobile  │  │ API    │  │ Webhook      │  │
│  │ Users   │  │ (Admin)  │  │  App    │  │ Client │  │ (External)   │  │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └───┬────┘  └──────┬───────┘  │
│       │            │              │            │              │          │
└───────┼────────────┼──────────────┼────────────┼──────────────┼──────────┘
        │            │              │            │              │
        ▼            ▼              ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Gateway (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  /api/v1/line    │  /api/v1/dashboard  │  /api/v1/scraping  │ AI  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                           Request ID Middleware                         │
│                           Rate Limiting                                 │
│                           JWT Authentication                            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌─────────────────┐    ┌────────────────┐
│  LINE Service │    │ Dashboard       │    │ Scraping       │
│  - Messaging  │    │ Service         │    │ Service        │
│  - User Mgmt  │    │ - Users         │    │ - Job Queue    │
│  - Webhooks   │    │ - Stats         │    │ - Botsaurus    │
└───────┬───────┘    └────────┬────────┘    └───────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   PostgreSQL     │  │      Redis       │  │   External APIs  │
│   (Primary DB)   │  │   (Cache + MQ)   │  │   - LINE API     │
│                  │  │                  │  │   - OpenAI API   │
│   - Users        │  │   - Celery       │  │   - Scraping     │
│   - LINE Users   │  │     Broker       │  │     Targets      │
│   - Jobs         │  │   - Cache        │  │                  │
│   - Conversations│  │   - Sessions     │  └──────────────────┘
└──────────────────┘  └──────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Celery Worker   │  │  Celery Beat     │  │   Scraping       │
│  - Async Tasks   │  │  - Scheduled     │  │   Pipeline       │
│  - LINE Messages│  │    Tasks         │  │   - Spiders      │
│  - AI Processing │  │                  │  │   - Pipelines    │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Component Details

### API Layer (FastAPI)
- **app/main.py**: FastAPI application entry point
- **Request ID Middleware**: Adds unique ID to every request for tracing
- **Structured Logging**: JSON logs with request context
- **CORS Middleware**: Configured for allowed origins
- **Error Handlers**: Consistent error response format

### Services Layer
- **LINE Service**: LINE Bot API integration
  - User management
  - Message sending (text, flex, template)
  - OAuth flow handling
- **Dashboard Service**: Admin dashboard operations
  - User CRUD
  - Statistics aggregation
  - Operation logging
- **Scraping Service**: Web scraping management
  - Job queue management
  - Botsaurus integration
  - Result storage
- **AI Service**: AI-powered features
  - LangGraph agent integration
  - Conversation management
  - OpenAI API calls

### Data Layer
- **PostgreSQL**: Primary database
  - Users, LINE users, scraping jobs, AI conversations
  - Full-text search capabilities
  - Transaction support
- **Redis**: Cache and message queue
  - Celery broker
  - Session cache
  - Rate limiting

### Task Queue (Celery)
- **Web**: API request handling
- **Worker**: Async task processing
- **Beat**: Scheduled tasks

## Data Flow

### LINE Message Flow
```
LINE User → LINE Server → Webhook → FastAPI → LINE Service →
  → Celery Task → Process Message → LINE Service → Send Reply
```

### Scraping Flow
```
User → API → Scraping Service → Create Job →
  → Celery Task → Botsaurus Spider → Results →
  → Database → Notify User
```

### AI Chat Flow
```
User → API → AI Service → Create/Update Conversation →
  → Celery Task → OpenAI/LangGraph → Response →
  → Save to Database → Return to User
```

## Security

### Authentication
- JWT tokens with HS256 algorithm
- Token expiration: 7 days
- Refresh tokens: 30 days

### Authorization
- Role-based access control
- Superuser for admin functions
- LINE user binding for LINE-specific features

### API Security
- Rate limiting: 60 requests/minute
- Request validation with Pydantic
- SQL injection prevention via SQLAlchemy
- XSS protection

### External API Protection
- Circuit breaker for LINE/OpenAI calls
- Retry with exponential backoff
- Request timeout handling

## Scalability

### Horizontal Scaling
- Multiple web replicas (load balancer)
- Multiple worker instances
- Redis Pub/Sub for inter-instance communication

### Caching Strategy
- Redis for frequently accessed data
- ETag support for API responses
- Static file caching

### Database Optimization
- Indexing on common queries
- Connection pooling
- Query optimization

## Monitoring

### Health Checks
- `/health`: Basic health
- `/ready`: Readiness check (DB, Redis)

### Metrics
- Prometheus metrics endpoint
- Request/response timing
- Error rates
- Celery task statistics

### Logging
- Structured JSON logs
- Request ID tracking
- Error stack traces
- Log levels: DEBUG, INFO, WARNING, ERROR