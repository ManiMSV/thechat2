# Architecture — ChatApp

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Diagram](#2-high-level-diagram)
3. [Frontend](#3-frontend)
4. [Backend](#4-backend)
5. [Database](#5-database)
6. [Authentication Flow](#6-authentication-flow)
7. [Real-Time Messaging Flow](#7-real-time-messaging-flow)
8. [API Reference](#8-api-reference)
9. [Data Models](#9-data-models)
10. [Key Design Decisions](#10-key-design-decisions)

---

## 1. System Overview

ChatApp is a browser-based real-time messaging application. It is split into three independent deployment units:

| Unit | Technology | Role |
|------|-----------|------|
| **Frontend** | Angular 19 SPA | UI, routing, state management |
| **Backend** | FastAPI (Python) | REST API + WebSocket server |
| **Database** | MongoDB Atlas | Persistent storage |

All communication between frontend and backend uses:
- **HTTPS REST** for CRUD operations (login, conversations, message history)
- **WSS WebSocket** for real-time message delivery

---

## 2. High-Level Diagram

```
┌──────────────────────────────────────────────────┐
│                  User's Browser                  │
│                                                  │
│   Angular SPA  (GitHub Pages / ng serve)         │
│   ┌──────────────┐   ┌───────────────────────┐   │
│   │  Auth Pages  │   │   Chat Dashboard      │   │
│   │  /login      │   │   /chat               │   │
│   │  /register   │   │   ConversationList    │   │
│   └──────┬───────┘   │   ChatWindow          │   │
│          │           └──────────┬────────────┘   │
│          │ REST (JWT)           │ REST + WSS      │
└──────────┼──────────────────────┼────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────────────────────────────────────┐
│            FastAPI Backend  (Render / uvicorn)   │
│                                                  │
│  ┌──────────────────┐  ┌────────────────────┐    │
│  │   REST Routers   │  │  WebSocket Router  │    │
│  │  /auth           │  │  /ws/{conv_id}     │    │
│  │  /users          │  │                    │    │
│  │  /conversations  │  │  ConnectionManager │    │
│  │  /messages       │  │  (in-memory map)   │    │
│  └────────┬─────────┘  └────────┬───────────┘    │
│           │                     │                │
└───────────┼─────────────────────┼────────────────┘
            │                     │
            ▼                     ▼
┌──────────────────────────────────────────────────┐
│              MongoDB Atlas  (Free tier)          │
│                                                  │
│  Collections:  users · conversations · messages  │
└──────────────────────────────────────────────────┘
```

---

## 3. Frontend

### Stack

| Item | Detail |
|------|--------|
| Framework | Angular 19 |
| Language | TypeScript 5.7 |
| HTTP | `@angular/common/http` (`HttpClient`) |
| Real-time | Native browser `WebSocket` |
| State | Service-level RxJS `BehaviorSubject` / `Subject` |
| Auth guard | `CanActivateFn` reading JWT from `localStorage` |
| Dev proxy | `proxy.conf.json` — rewrites `/api/*` → `http://localhost:8000/*` |

### Directory Layout

```
src/app/
├── core/
│   ├── auth.service.ts          # Login, register, token management
│   ├── auth.guard.ts            # Route guard
│   ├── chat.service.ts          # REST calls: conversations & messages
│   ├── jwt.interceptor.ts       # Attaches Bearer token to every request
│   └── websocket.service.ts     # WebSocket connect / send / reconnect
├── features/
│   ├── auth/
│   │   ├── login/               # LoginComponent
│   │   └── register/            # RegisterComponent
│   └── chat/
│       ├── chat-shell/          # Layout shell — sidebar + outlet
│       ├── conversation-list/   # Left-panel: list of conversations
│       ├── chat-window/         # Right-panel: message thread
│       └── new-chat-modal/      # Search users, start conversation
└── shared/models/
    ├── user.model.ts
    ├── conversation.model.ts
    └── message.model.ts
```

### Data Flow (REST)

```
Component → ChatService.getConversations()
         → HttpClient.get('/api/conversations')
         → JwtInterceptor adds Authorization header
         → Proxy rewrites to http://localhost:8000/conversations
         → FastAPI responds
         → Observable resolves in component
```

### WebSocket Lifecycle

1. `ChatWindowComponent` calls `WebsocketService.connect(conversationId, token)`
2. Service opens `wss://<host>/api/ws/<conversationId>?token=<jwt>`
3. Incoming JSON frames pushed to `messages$` Subject
4. Component subscribes via `onMessage()` Observable
5. On disconnect: exponential back-off reconnect (1 s → 30 s max)
6. Component `ngOnDestroy` calls `WebsocketService.close()`

---

## 4. Backend

### Stack

| Item | Detail |
|------|--------|
| Framework | FastAPI |
| Server | Uvicorn (ASGI) |
| ODM | Motor (async MongoDB driver) |
| Auth | `python-jose` (JWT) + `bcrypt` |
| Config | `python-dotenv` — `.env` file |

### Module Layout

```
backend/
├── main.py               # App factory, CORS, router registration, lifespan
├── auth.py               # JWT encode/decode, bcrypt hash/verify
├── database.py           # Motor client, db handle, index creation
├── models.py             # Pydantic request/response models
├── dependencies.py       # FastAPI dependency: get_current_user
├── connection_manager.py # In-memory WebSocket room manager
└── routers/
    ├── auth.py           # POST /auth/register, POST /auth/login
    ├── users.py          # GET /users/search, GET /users/{id}
    ├── conversations.py  # GET/POST /conversations, POST /conversations/{id}/messages/read
    ├── messages.py       # GET /conversations/{id}/messages, POST /conversations/{id}/messages
    └── websocket.py      # WS /ws/{conversation_id}?token=
```

### Request Lifecycle

```
HTTP Request
  → CORSMiddleware
  → Router match
  → Dependency injection (get_current_user decodes JWT → fetches user from DB)
  → Route handler
  → Motor async DB call
  → Pydantic response model serialization
  → Response
```

### Connection Manager

`ConnectionManager` holds an in-memory `dict[conversation_id → list[WebSocket]]`.

- On message received: persists to MongoDB, then calls `manager.broadcast()` — iterates all sockets in the room and sends JSON.
- Dead sockets (send failure) are removed automatically.
- **Note:** this is a single-process model. Horizontal scaling requires replacing the manager with a Redis pub/sub backend.

### CORS

Allowed origins are built dynamically at startup:

```
["http://localhost:4200", "http://127.0.0.1:4200"]
+ CORS_ORIGINS env var (comma-separated)
```

---

## 5. Database

### MongoDB Collections

#### `users`
| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | Primary key |
| `username` | string | Unique, 3–20 chars, `\w+` |
| `email` | string | Unique |
| `password_hash` | string | bcrypt |
| `avatar_url` | string? | Optional |
| `created_at` | datetime | |
| `updated_at` | datetime | |

**Indexes:** `email` (unique), `username` (unique)

#### `conversations`
| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `participants` | `[userId, userId]` | Array of two user ID strings |
| `created_at` | datetime | |
| `last_message_at` | datetime | Updated on every new message |

**Indexes:** `participants`

#### `messages`
| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `conversation_id` | string | FK → conversations |
| `sender_id` | string | FK → users |
| `content` | string | |
| `created_at` | datetime | |
| `read_by` | `[userId, …]` | IDs of users who have read it |

**Indexes:** `conversation_id`, compound `(conversation_id, created_at)` for paginated history

---

## 6. Authentication Flow

```
Register
  Client → POST /auth/register {username, email, password}
         ← 201 {id, username, email}

Login
  Client → POST /auth/login {email, password}
  Backend: fetch user by email
           bcrypt verify password
           create JWT {sub: user_id, exp: now+24h}
         ← 200 {access_token, token_type: "bearer"}

Authenticated Request
  Client adds header:  Authorization: Bearer <jwt>
  Backend dependency:  decode JWT → ObjectId → DB lookup → UserInDB
```

JWT is stored in browser `localStorage`. The `JwtInterceptor` attaches it automatically to every `HttpClient` request.

Token expiry: **24 hours** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

---

## 7. Real-Time Messaging Flow

```
1. Client opens WebSocket:
   wss://backend/ws/<conversation_id>?token=<jwt>

2. Backend validates token → verifies user is a participant → accepts socket.

3. Client sends:
   { "type": "message", "content": "Hello!" }

4. Backend:
   a. Saves message document to MongoDB
   b. Updates conversation.last_message_at
   c. Broadcasts to all sockets in the room:
      {
        "type": "message",
        "id": "<new_message_id>",
        "conversation_id": "...",
        "sender_id": "...",
        "content": "Hello!",
        "created_at": "<iso>",
        "read_by": ["<sender_id>"]
      }

5. All participants (including sender) render the message from the broadcast.
```

---

## 8. API Reference

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Get JWT |

### Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users/search?q=` | JWT | Search users by username/email |
| GET | `/users/{id}` | JWT | Get user profile |

### Conversations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/conversations` | JWT | List caller's conversations |
| POST | `/conversations` | JWT | Start or retrieve conversation |
| POST | `/conversations/{id}/messages/read` | JWT | Mark messages as read |

### Messages

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/conversations/{id}/messages` | JWT | Fetch message history |
| POST | `/conversations/{id}/messages` | JWT | Send message (REST fallback) |

### WebSocket

| Protocol | Path | Query Param | Description |
|----------|------|-------------|-------------|
| WS/WSS | `/ws/{conversation_id}` | `token=<jwt>` | Real-time message channel |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status": "ok"}` |

---

## 9. Data Models

### Pydantic (Backend)

```
UserCreate       username, email, password
LoginRequest     email, password
UserPublic       id, username, email, avatar_url
ConversationPublic  id, participants, created_at, last_message_at,
                    other_user (UserPublic), last_message_preview, unread_count
MessageCreate    content
MessagePublic    id, conversation_id, sender_id, content, created_at, read_by
```

### TypeScript Interfaces (Frontend)

Located in `src/app/shared/models/`:

```
User            id, username, email, avatarUrl?
Conversation    id, participants, otherUser, lastMessagePreview?, unreadCount, lastMessageAt
Message         id, conversationId, senderId, content, createdAt, readBy
```

---

## 10. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| FastAPI over Django | Async-native, WebSocket support built-in, less boilerplate |
| Motor (async) driver | Non-blocking DB calls on asyncio event loop |
| JWT in localStorage | Simple; acceptable for v1. Move to httpOnly cookie for higher security |
| In-memory ConnectionManager | Simplest viable real-time for single-process deploy on Render free tier |
| Angular dev proxy | Avoids CORS in development; production uses same-host reverse proxy or explicit CORS_ORIGINS |
| bcrypt password hashing | Industry-standard; input truncated to 72 bytes (bcrypt limit) |
| Exponential back-off reconnect | Graceful recovery from transient network loss without overwhelming server |
