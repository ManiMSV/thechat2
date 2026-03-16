# Product Requirements Document (PRD)
## ChatApp — Real-Time Messaging Platform

---

**Document Version:** 1.0  
**Date:** 2026-03-11  
**Status:** Draft  

---

## Table of Contents

1. [Overview](#1-overview)
2. [Goals & Success Metrics](#2-goals--success-metrics)
3. [Tech Stack](#3-tech-stack)
4. [System Architecture](#4-system-architecture)
5. [Features & Requirements](#5-features--requirements)
   - 5.1 Authentication
   - 5.2 Main Window / Dashboard
   - 5.3 Chat Window
   - 5.4 Notifications
6. [Data Models](#6-data-models)
7. [API Endpoints](#7-api-endpoints)
8. [Frontend Pages & Components](#8-frontend-pages--components)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Scalability Considerations](#10-scalability-considerations)
11. [Deployment Plan](#11-deployment-plan)
12. [Future Ideas Backlog](#12-future-ideas-backlog)
13. [Out of Scope (v1)](#13-out-of-scope-v1)

---

## 1. Overview

**ChatApp** is a real-time messaging web application that allows users to register, log in, and exchange messages with other users. The v1 focuses on a clean, functional chat experience — contact list, chat history, and real-time messaging — with a scalable architecture ready for future feature expansion.

### Target Users
- Any individual wanting to send and receive messages via a browser-based interface.

---

## 2. Goals & Success Metrics

| Goal | Metric |
|------|--------|
| Users can register and log in securely | Auth flow works end-to-end with JWT |
| Users can send and receive messages in real time | Messages appear within < 1 second |
| Chat history is persisted | Messages survive page refresh |
| App is deployable to free/low-cost cloud | GitHub Pages (frontend) + Render (backend) |
| Codebase is structured for future scalability | Modular Angular services + FastAPI routers |

---

## 3. Tech Stack

| Layer | Technology | Hosting |
|-------|-----------|---------|
| **Frontend** | Angular (latest stable) | GitHub Pages |
| **Backend** | FastAPI (Python) | Render (Free/Starter tier) |
| **Database** | MongoDB | MongoDB Atlas (Free tier) |
| **Real-time** | WebSockets (FastAPI native) | Via Render |
| **Auth** | JWT (JSON Web Tokens) | Stateless, stored in localStorage |
| **API Communication** | REST + WebSocket | HTTPS / WSS |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────┐
│              User's Browser                 │
│                                             │
│   Angular SPA (GitHub Pages)                │
│   ┌────────────┐  ┌──────────────────────┐  │
│   │ Auth Pages │  │  Chat Dashboard      │  │
│   └────────────┘  └──────────────────────┘  │
│          │  REST            │  WebSocket     │
└──────────┼──────────────────┼────────────────┘
           │                  │
           ▼                  ▼
┌─────────────────────────────────────────────┐
│         FastAPI Backend (Render)            │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  REST API   │  │  WebSocket Manager   │  │
│  │  /auth      │  │  /ws/{room_id}       │  │
│  │  /users     │  └──────────────────────┘  │
│  │  /messages  │                            │
│  └─────────────┘                            │
│          │                                  │
└──────────┼──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│        MongoDB Atlas (Cloud)                │
│                                             │
│  Collections:                               │
│  - users                                    │
│  - messages                                 │
│  - conversations                            │
└─────────────────────────────────────────────┘
```

**Key design decisions:**
- **Stateless JWT auth** — backend doesn't store sessions; any backend instance can verify a token.
- **WebSocket per conversation** — each open chat connects to a WebSocket room identified by a `conversation_id`.
- **REST for non-real-time** — login, registration, fetching contact list, message history.

---

## 5. Features & Requirements

### 5.1 Authentication

#### 5.1.1 Register

- **Page:** `/register`
- **Fields:** `username` (unique), `email` (unique), `password`
- **Validation:**
  - Username: 3–20 characters, alphanumeric + underscores
  - Email: valid format
  - Password: minimum 8 characters
- **On success:** Redirect to `/login` with a success message
- **On failure:** Show inline field-level error messages

#### 5.1.2 Login

- **Page:** `/login`
- **Fields:** `email`, `password`
- **On success:**
  - Receive `access_token` (JWT) from backend
  - Store token in `localStorage`
  - Redirect to `/chat` (main dashboard)
- **On failure:** Show generic error ("Invalid email or password")

#### 5.1.3 Logout

- Clear JWT from `localStorage`
- Redirect to `/login`

#### 5.1.4 Route Guards

- All `/chat/*` routes require a valid JWT
- Unauthenticated users are redirected to `/login`

---

### 5.2 Main Window / Dashboard

- **Route:** `/chat`
- **Layout:** Two-panel layout
  - **Left Panel:** Contact / Conversation List
  - **Right Panel:** Active Chat Window (or a welcome screen if none selected)

#### Left Panel — Conversation List

- Displays all existing conversations for the logged-in user
- Each conversation item shows:
  - Contact's username / avatar initials
  - Last message preview (truncated to 40 chars)
  - Timestamp of last message
  - Unread message badge (count)
- Conversations are sorted by most recent message (descending)
- **New Chat Button** — opens a modal/dialog to start a new conversation (search by username)
- **Logout button** in sidebar/header

#### Right Panel — Chat Window

- Shows when a conversation is selected from the list
- Displays full message history (paginated or lazy-loaded, oldest at top)
- Message input bar at the bottom with send button (also sends on `Enter`)
- Shows sender name and timestamp per message
- Real-time updates via WebSocket for new incoming messages

---

### 5.3 Chat Window (Detail)

| Element | Behaviour |
|---------|-----------|
| Message bubble (sent) | Right-aligned, primary colour |
| Message bubble (received) | Left-aligned, neutral colour |
| Timestamp | Shown per message or grouped by day |
| Send button | Disabled if input is empty |
| WebSocket connection | Opens on conversation select, closes on navigate away |
| Reconnection | Auto-reconnect with exponential backoff on disconnect |

---

### 5.4 Notifications (Basic — v1)

- Browser tab title updates to show unread count (e.g., `(3) ChatApp`)
- Unread badge on conversation list item updates in real time via WebSocket

---

## 6. Data Models

### User

```json
{
  "_id": "ObjectId",
  "username": "string (unique)",
  "email": "string (unique)",
  "password_hash": "string (bcrypt)",
  "avatar_url": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Conversation

```json
{
  "_id": "ObjectId",
  "participants": ["user_id_1", "user_id_2"],
  "created_at": "datetime",
  "last_message_at": "datetime"
}
```

> For v1, a conversation is always between exactly 2 participants (1-on-1 DM). Group chat support is a future feature.

### Message

```json
{
  "_id": "ObjectId",
  "conversation_id": "ObjectId",
  "sender_id": "ObjectId",
  "content": "string",
  "created_at": "datetime",
  "read_by": ["user_id"]
}
```

---

## 7. API Endpoints

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login, returns JWT |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/me` | Get current user profile |
| `GET` | `/users/search?q={username}` | Search users by username (for new chat) |

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/conversations` | Get all conversations for current user |
| `POST` | `/conversations` | Create or get existing conversation with another user |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/conversations/{id}/messages` | Get paginated message history |
| `POST` | `/conversations/{id}/messages` | Send a message (fallback if WebSocket fails) |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /ws/{conversation_id}?token={jwt}` | Real-time message channel for a conversation |

---

## 8. Frontend Pages & Components

### Angular Module Structure

```
src/app/
├── core/
│   ├── auth.service.ts          # Login, register, token management
│   ├── chat.service.ts          # REST calls for conversations & messages
│   ├── websocket.service.ts     # WebSocket connection management
│   ├── auth.guard.ts            # Route protection
│   └── interceptors/
│       └── jwt.interceptor.ts   # Attaches Authorization header to requests
│
├── features/
│   ├── auth/
│   │   ├── login/               # LoginComponent
│   │   └── register/            # RegisterComponent
│   │
│   └── chat/
│       ├── chat-shell/          # Main two-panel layout
│       ├── conversation-list/   # Left panel list
│       ├── conversation-item/   # Single row in list
│       ├── chat-window/         # Right panel
│       ├── message-bubble/      # Individual message
│       ├── message-input/       # Text input + send button
│       └── new-chat-modal/      # Modal to start a new conversation
│
└── shared/
    ├── components/
    │   └── avatar/              # Initials-based avatar
    └── models/
        ├── user.model.ts
        ├── conversation.model.ts
        └── message.model.ts
```

### Routing

```
/                → redirect to /chat
/login           → LoginComponent
/register        → RegisterComponent
/chat            → ChatShellComponent (guarded)
  /chat/:id      → ChatShellComponent with active conversation
```

---

## 9. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Performance** | Initial page load < 3s on average connection |
| **Security** | Passwords hashed with bcrypt (cost ≥ 12); JWT signed with HS256 secret |
| **CORS** | Backend allows only GitHub Pages origin (and localhost for dev) |
| **Input sanitisation** | All user input sanitised on backend before DB write |
| **HTTPS / WSS** | All traffic encrypted; Render provides TLS by default |
| **Environment config** | Secrets (DB URI, JWT secret) stored in Render environment variables, never in code |
| **Error handling** | Backend returns consistent error shape: `{ "detail": "message" }` |
| **Logging** | FastAPI logs all requests; errors logged with stack trace |

---

## 10. Scalability Considerations

The following decisions are made specifically to allow the app to grow:

### Backend
- **FastAPI routers** — each feature (auth, users, conversations, messages) is its own router module, making it easy to add features without touching unrelated code.
- **Dependency injection** — database and auth dependencies are injected via FastAPI's `Depends()`, making them swappable.
- **WebSocket manager** — the `ConnectionManager` class (manages active WS connections) can later be replaced with a Redis Pub/Sub layer to support multiple backend instances.
- **MongoDB schema** — documents are flexible; new fields can be added without migrations.
- **Pagination** — message history endpoint uses cursor-based pagination from day one.

### Frontend
- **Angular lazy loading** — `auth` and `chat` feature modules are lazy-loaded.
- **Service abstraction** — all API calls go through service classes, not directly in components.
- **Environment files** — `environment.ts` / `environment.prod.ts` for managing API base URLs.

### Infrastructure
- **Render** — can scale to paid tiers or switch to any Docker-compatible host with no code changes.
- **MongoDB Atlas** — can be scaled vertically (instance size) or horizontally (sharding) as needed.

---

## 11. Deployment Plan

### Frontend — GitHub Pages

1. Build Angular with `ng build --configuration production`
2. Output goes to `dist/` directory
3. Use `angular-cli-ghpages` (`npx angular-cli-ghpages --dir=dist/<app-name>`) to deploy to `gh-pages` branch
4. Set `base-href` to match the GitHub Pages URL: `ng build --base-href /repo-name/`
5. Configure `404.html` redirect hack for Angular client-side routing on GitHub Pages

### Backend — Render

1. Connect GitHub repo to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in Render dashboard:
   - `MONGODB_URI`
   - `JWT_SECRET`
   - `ALLOWED_ORIGINS` (GitHub Pages URL)
5. Render auto-deploys on every push to `main`

### Database — MongoDB Atlas

1. Create free M0 cluster on MongoDB Atlas
2. Create a DB user with read/write permissions
3. Whitelist Render's outbound IPs (or allow all: `0.0.0.0/0` for simplicity in dev)
4. Copy connection string to Render environment variable `MONGODB_URI`

---

## 12. Future Ideas Backlog

These are not in scope for v1 but the architecture is designed to accommodate them:

| Feature | Notes |
|---------|-------|
| Group chats | Conversations already support N participants in the data model |
| Message read receipts | `read_by` field already exists in Message model |
| Typing indicators | Send a WebSocket event type `"typing"` alongside `"message"` |
| File / image sharing | Add `attachments` array to Message model; store files in S3/Cloudflare R2 |
| Push notifications | Integrate Web Push API or a service like Firebase Cloud Messaging |
| Message reactions (emoji) | Add `reactions` map to Message model |
| User status (online/offline) | Track via WebSocket connect/disconnect events |
| Block / report users | Add `blocked_users` list to User model |
| Message search | MongoDB Atlas Search (Lucene-based) can be enabled on the messages collection |
| Mobile app | Backend is already REST + WebSocket — usable from React Native / Flutter |
| End-to-end encryption | Requires key exchange protocol (e.g., Signal Protocol) — significant rework |
| OAuth login (Google, GitHub) | Add OAuth2 flow alongside existing email/password auth |

---

## 13. Out of Scope (v1)

- Group chats (more than 2 participants)
- Voice or video calls
- File/image uploads
- Mobile native apps
- Admin dashboard
- Email verification on registration
- Password reset flow
- Message deletion / editing

---

*End of Document*
