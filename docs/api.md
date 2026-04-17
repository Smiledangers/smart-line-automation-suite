# API Reference

Complete API documentation for Smart LINE Bot + Dashboard + Scraper Pipeline.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@example.com&password=changeme
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

## LINE Endpoints

### Webhook
```http
POST /line/webhook
Content-Type: application/json

{
  "destination": "U1234567890",
  "events": [...]
}
```

### Send Message
```http
POST /line/send
Authorization: Bearer {token}
Content-Type: application/json

{
  "line_user_id": "U1234567890",
  "message": "Hello!"
}
```

### Get LINE Users
```http
GET /line/users
Authorization: Bearer {token}
```

### LINE Callback (OAuth)
```http
GET /line/callback?code=xxx&state=xxx
```

## Dashboard Endpoints

### Get Users
```http
GET /dashboard/users
Authorization: Bearer {token}
```

Response:
```json
{
  "users": [
    {
      "id": 1,
      "email": "admin@example.com",
      "full_name": "Admin",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 1
}
```

### Get Statistics
```http
GET /dashboard/stats
Authorization: Bearer {token}
```

Response:
```json
{
  "user_count": 10,
  "line_user_count": 50,
  "scraping_job_count": 100,
  "completed_job_count": 80,
  "ai_conversation_count": 200
}
```

### Create User
```http
POST /dashboard/users
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "password123",
  "full_name": "New User"
}
```

## Scraping Endpoints

### Create Job
```http
POST /scraping/jobs
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://example.com",
  "website_type": "generic",
  "priority": 1
}
```

### Get Jobs
```http
GET /scraping/jobs
Authorization: Bearer {token}
```

### Get Job Detail
```http
GET /scraping/jobs/{job_id}
Authorization: Bearer {token}
```

### Get Job Results
```http
GET /scraping/jobs/{job_id}/results
Authorization: Bearer {token}
```

### Cancel Job
```http
POST /scraping/jobs/{job_id}/cancel
Authorization: Bearer {token}
```

## AI Endpoints

### Create Conversation
```http
POST /ai/conversations
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "My Chat"
}
```

### Get Conversations
```http
GET /ai/conversations
Authorization: Bearer {token}
```

### Chat
```http
POST /ai/chat
Authorization: Bearer {token}
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "conversation_id": 1
}
```

Response:
```json
{
  "message": "I'm doing well, thank you!",
  "conversation_id": 1,
  "message_id": "msg_123"
}
```

### Get Conversation History
```http
GET /ai/conversations/{conversation_id}/history
Authorization: Bearer {token}
```

## Health Check

### Health
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Ready
```http
GET /ready
```

## Error Responses

All endpoints may return the following error codes:

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

Error Response Format:
```json
{
  "detail": "Error message here"
}
```