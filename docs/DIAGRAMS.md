# PostPilot AI — Architecture Diagrams

Auto-generated from source code analysis. All flows reflect actual implementation in `backend/app/` and `frontend/src/`.

---

## 1. System Architecture

```mermaid
flowchart LR
    subgraph Client["Frontend (React + Vite)"]
        FE_Login[LoginPage]
        FE_Cmd[CommandPage]
        FE_Dash[DashboardPage]
        FE_JobDetail[JobDetailPage]
        FE_FB[FacebookSetupPage]
        FE_Auth[Zustand authStore]
        FE_Job[Zustand jobStore]
        FE_API[axios + ssePost client]
    end

    subgraph Backend["Backend (FastAPI)"]
        API_Auth[/auth router/]
        API_Jobs[/jobs router/]
        API_FB[/facebook router/]
        SVC_NLU[nlu_parser]
        SVC_Plan[plan_generator]
        SVC_Content[content_gen]
        SVC_FBPost[fb_poster]
        SVC_Sched[APScheduler tick]
        AI_Factory[AI Provider Factory]
        DB[(SQLAlchemy / Alembic<br/>users, facebook_pages,<br/>jobs, job_posts)]
    end

    subgraph External["External APIs"]
        OpenAI[OpenAI<br/>gpt-4o / gpt-image]
        Gemini[Gemini<br/>1.5-pro / imagen-3]
        FB_Graph[Facebook Graph API v19.0]
    end

    FE_Login --> FE_Auth
    FE_Cmd --> FE_API
    FE_Dash --> FE_API
    FE_JobDetail --> FE_API
    FE_FB --> FE_API
    FE_Job -.consumed by.- FE_Dash
    FE_Job -.consumed by.- FE_JobDetail

    FE_API -->|JWT Bearer| API_Auth
    FE_API -->|SSE + REST| API_Jobs
    FE_API -->|REST| API_FB

    API_Jobs --> SVC_NLU
    API_Jobs --> SVC_Plan
    API_Jobs --> SVC_Content
    API_FB --> SVC_FBPost
    SVC_Sched --> SVC_Content
    SVC_Sched --> SVC_FBPost

    SVC_NLU --> OpenAI
    SVC_Content --> AI_Factory
    AI_Factory --> OpenAI
    AI_Factory --> Gemini
    SVC_FBPost --> FB_Graph

    API_Auth --> DB
    API_Jobs --> DB
    API_FB --> DB
    SVC_Sched --> DB
```

---

## 2. Data Model (ER)

```mermaid
erDiagram
    USER ||--o{ JOB : owns
    USER ||--o| FACEBOOK_PAGE : has
    JOB ||--o{ JOB_POST : contains

    USER {
        int id PK
        string username
        string hashed_password
        bool is_active
        datetime created_at
    }
    FACEBOOK_PAGE {
        int id PK
        int user_id FK
        string page_id
        string page_name
        text access_token
        datetime token_expires_at
    }
    JOB {
        int id PK
        int user_id FK
        string title
        text raw_input
        json parsed_config
        enum status "DRAFT|SCHEDULED|RUNNING|DONE|PAUSED"
        json style_profile
        datetime created_at
    }
    JOB_POST {
        int id PK
        int job_id FK
        int day_index
        int post_order
        text content_text
        text original_content_text
        text image_url
        text image_prompt
        text image_style_note
        datetime scheduled_time
        enum status "PENDING|APPROVED|POSTED|FAILED"
        string fb_post_id
        text error_message
        datetime posted_at
        datetime approved_at
    }
```

---

## 3. Agent Workflow / Logic Flow (PRIMARY)

PostPilot is a **single-shot LLM-orchestrated content pipeline** (not LangGraph / not ReAct multi-agent). The "agent" is a deterministic FastAPI orchestrator that invokes specialized LLM steps: NLU parser → planner → text generator → image-prompt developer → image generator → style profile extractor. APScheduler acts as a periodic executor that triggers downstream generation + posting.

```mermaid
flowchart TD
    A[User Input<br/>natural language command]
    B[CommandPage<br/>ssePost /jobs/parse]
    C[NLU Parser<br/>gpt-4o-mini, JSON mode]
    D[Normalize + Validate<br/>_normalize_config]
    E{Parse OK?}
    F[_default_config fallback]
    G[Create Job DRAFT<br/>+ plan_generator slots]
    H[SSE done event<br/>JobPreview UI]
    I[User reviews / edits<br/>PUT /jobs/:id/posts/:pid]
    J[Confirm<br/>ssePost /jobs/:id/confirm]
    K[generate_day_content Day 1<br/>skip_images=true]
    L[Text Provider<br/>complete via AI Factory<br/>openai or gemini]
    M[Append hashtags from tags]
    N[Job status SCHEDULED]
    O[Dashboard / JobDetail]

    P[Per-post user actions]
    Q[regenerate-image]
    R[generate_image_prompt<br/>mini model develops prompt]
    S[Image Provider<br/>gpt-image-2 / dall-e-3 / imagen]
    T[approve post<br/>status APPROVED]
    U{Day 1 edited?<br/>tone not in style_profile}
    V[Background task<br/>generate_style_profile<br/>diff original vs edited]
    W[Save style_profile to Job<br/>tone/format/length/structure]

    X[APScheduler tick<br/>every 60s]
    Y[Task 3: lookahead 60min<br/>find empty PENDING posts]
    Z[generate_day_content<br/>uses job.style_profile]
    AA[Task 1: APPROVED due<br/>+ Task 2: PENDING overdue fallback]
    AB[fb_poster.post_to_facebook]
    AC{image_url type?}
    AD[POST /PAGE/feed<br/>text only]
    AE[POST /PAGE/photos<br/>url field]
    AF[POST /PAGE/photos<br/>multipart bytes<br/>base64 data URI]
    AG[Update JobPost POSTED / FAILED]
    AH[_check_job_completion<br/>all done -> Job DONE]

    A --> B --> C --> D --> E
    E -->|exception| F --> G
    E -->|ok| G --> H --> I --> J --> K --> L --> M --> N --> O

    O --> P
    P --> Q --> R --> S
    P --> T --> U
    U -->|yes| V --> W
    U -->|no| AH

    X --> Y --> Z --> L
    X --> AA --> AB --> AC
    AC -->|none| AD --> AG
    AC -->|http url| AE --> AG
    AC -->|data: base64| AF --> AG
    AG --> AH
```

---

## 4. SSE Streaming Sequence — /jobs/parse

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant FE as CommandPage
    participant API as POST /jobs/parse
    participant NLU as nlu_parser
    participant OAI as OpenAI gpt-4o-mini
    participant PLN as plan_generator
    participant DB as Database

    U->>FE: types command, submit
    FE->>API: fetch (stream)
    API-->>FE: event: step {parsing}
    API->>NLU: parse_command(raw_input)
    NLU->>OAI: chat.completions (json_object)
    OAI-->>NLU: ParsedConfig JSON
    NLU-->>API: ParsedConfig (or default on error)
    API-->>FE: event: step {parsed, config}
    API-->>FE: event: step {scheduling}
    API->>DB: INSERT Job (DRAFT)
    API->>PLN: generate_schedule(config)
    PLN-->>API: slot list
    API->>DB: INSERT JobPost rows (PENDING, no content)
    API-->>FE: event: done {job_id, config, posts}
    FE->>U: render JobPreview
```

---

## 5. Confirm + Day-1 Generation Sequence — /jobs/:id/confirm

```mermaid
sequenceDiagram
    autonumber
    participant FE as CommandPage
    participant API as POST /jobs/:id/confirm
    participant CG as content_gen.generate_day_content
    participant TP as TextProvider (AI Factory)
    participant DB as Database

    FE->>API: ssePost confirm
    API->>DB: load Job (must be DRAFT)
    API-->>FE: event: step {generating, current:0, total:N}
    API->>CG: generate_day_content(day=1, skip_images=true)
    loop each post_order
        CG->>TP: complete(system, user prompt + style_profile)
        TP-->>CG: text
        CG->>CG: append hashtags from tags
    end
    CG-->>API: results
    API->>DB: UPDATE JobPost.content_text + original_content_text
    API->>DB: Job.status = SCHEDULED
    API-->>FE: event: step {complete}
    API-->>FE: event: done {status:SCHEDULED}
    FE->>FE: navigate /dashboard
```

---

## 6. APScheduler Tick (every 60s)

```mermaid
flowchart TD
    T[Scheduler tick<br/>_post_due_items] --> T1[Task 1<br/>JobPost.status=APPROVED<br/>AND scheduled_time<=now]
    T --> T2[Task 2 fallback<br/>JobPost.status=PENDING<br/>content_text NOT NULL<br/>AND scheduled_time<=now]
    T --> T3[Task 3<br/>JobPost.status=PENDING<br/>content_text IS NULL<br/>AND scheduled_time<=now+60min]

    T1 --> POST[_do_post]
    T2 --> POST
    POST --> FB[fb_poster.post_to_facebook]
    FB -->|ok| POSTED[status=POSTED<br/>fb_post_id, posted_at]
    FB -->|exception| FAIL[status=FAILED<br/>error_message]
    POSTED --> CHK[_check_job_completion]
    FAIL --> CHK
    CHK -->|no pending/approved left| DONE[Job.status=DONE]

    T3 --> GRP[groupby job_id, day_index]
    GRP --> GEN[generate_day_content<br/>style_profile from Job]
    GEN --> SAVE[UPDATE JobPost<br/>content_text + image_url + image_prompt]
```

---

## 7. AI Provider Abstraction

```mermaid
classDiagram
    class TextProvider {
        <<abstract>>
        +complete(system, user, model, temperature, max_tokens, json_mode) str
    }
    class ImageProvider {
        <<abstract>>
        +generate(prompt, model, size, quality, style) str
    }
    class OpenAITextProvider
    class GeminiTextProvider
    class OpenAIImageProvider
    class GeminiImageProvider
    class Factory {
        +get_text_provider() TextProvider
        +get_image_provider() ImageProvider
        +reset_providers()
    }

    TextProvider <|-- OpenAITextProvider
    TextProvider <|-- GeminiTextProvider
    ImageProvider <|-- OpenAIImageProvider
    ImageProvider <|-- GeminiImageProvider
    Factory ..> TextProvider : reads AI_TEXT_PROVIDER
    Factory ..> ImageProvider : reads AI_IMAGE_PROVIDER
```

Selection is env-driven (`AI_TEXT_PROVIDER`, `AI_IMAGE_PROVIDER`) and providers are module-level singletons cached after first init.

---

## 8. Job & Post State Machines

```mermaid
stateDiagram-v2
    [*] --> DRAFT: POST /jobs/parse
    DRAFT --> SCHEDULED: POST /jobs/:id/confirm
    DRAFT --> [*]: DELETE /jobs/:id
    SCHEDULED --> RUNNING: first post sent by scheduler
    SCHEDULED --> PAUSED: POST /jobs/:id/pause
    RUNNING --> PAUSED: POST /jobs/:id/pause
    PAUSED --> SCHEDULED: POST /jobs/:id/resume
    RUNNING --> DONE: all posts POSTED or FAILED
    SCHEDULED --> DONE: all posts POSTED or FAILED
```

```mermaid
stateDiagram-v2
    [*] --> PENDING: created by plan_generator
    PENDING --> APPROVED: POST /jobs/:id/posts/:pid/approve
    APPROVED --> POSTED: scheduler Task 1 + Graph API ok
    PENDING --> POSTED: scheduler Task 2 fallback ok
    APPROVED --> FAILED: Graph API error
    PENDING --> FAILED: Graph API error
```

---

## 9. Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as LoginPage
    participant API as POST /auth/login
    participant SEC as core.security
    participant DB as Database

    U->>FE: username + password
    FE->>API: { username, password }
    API->>DB: SELECT user WHERE username
    API->>SEC: verify_password(plain, hashed)
    SEC-->>API: bool
    API->>SEC: create_access_token({sub: username})
    SEC-->>API: JWT (HS256, 24h)
    API-->>FE: { access_token, user }
    FE->>FE: localStorage + Zustand authStore
    Note over FE: axios interceptor adds<br/>Authorization: Bearer <token><br/>on every request
    Note over FE: 401 response -> clear token<br/>redirect /login
```

---

## 10. Facebook Token Setup Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as FacebookSetupPage
    participant API as POST /facebook/setup-token
    participant FB as Graph API v19.0
    participant DB as Database

    U->>FE: paste short_lived_token + page_id
    FE->>API: { short_lived_token, page_id }
    API->>FB: GET /oauth/access_token<br/>grant_type=fb_exchange_token
    FB-->>API: long_lived_user_token (60d)
    API->>FB: GET /me/accounts
    FB-->>API: pages[] with page access_token
    API->>FB: GET /:page_id?fields=id,name
    FB-->>API: { id, name }
    API->>DB: UPSERT FacebookPage<br/>(user_id, page_id, page_name, access_token)
    API-->>FE: FacebookPageOut
```

---

## 11. Frontend Routing

```mermaid
flowchart LR
    R[BrowserRouter] --> L[/login -> LoginPage/]
    R --> C[/command -> CommandPage*/]
    R --> D[/dashboard -> DashboardPage*/]
    R --> J[/jobs/:id -> JobDetailPage*/]
    R --> F[/facebook-setup -> FacebookSetupPage*/]
    R --> NF[* -> Navigate /login]

    C -. wrapped by .-> PR[ProtectedRoute<br/>checks authStore.token]
    D -. wrapped by .-> PR
    J -. wrapped by .-> PR
    F -. wrapped by .-> PR
```

`*` = behind `ProtectedRoute` (redirects to `/login` when no token in Zustand authStore).

---

## 12. Style Profile Learning Loop

```mermaid
flowchart TD
    A[Day 1 generated<br/>original_content_text saved] --> B[User edits content_text]
    B --> C[User clicks Approve]
    C --> D{day_index == 1<br/>AND tone not in<br/>style_profile<br/>AND text changed?}
    D -->|no| E[Just mark APPROVED]
    D -->|yes| F[asyncio.create_task<br/>_extract_and_save_style_profile]
    F --> G[generate_style_profile<br/>mini model, JSON mode<br/>diff original vs edited]
    G --> H{no_changes?}
    H -->|yes| I[discard]
    H -->|no| J[Merge into Job.style_profile<br/>tone, format, length,<br/>structure, language_notes]
    J --> K[Future generate_day_content<br/>passes style_profile to LLM<br/>so Day 2+ matches user voice]
```

Image direction is captured separately: `image_style_note` from the Approve request is stored in `style_profile.image_direction` and consumed by `generate_image_prompt` as `[Style instruction]`.

---

## 13. Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, React Router, Zustand, axios, framer-motion, TailwindCSS |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic v2, APScheduler (AsyncIO), httpx |
| Auth | OAuth2PasswordBearer + JWT (HS256, 24h) via `python-jose` style helpers in `core.security` |
| DB | SQLite default (`postpilot.db`), Postgres-ready via `DATABASE_URL` |
| LLM (text) | OpenAI `gpt-4o` / `gpt-4o-mini` OR Gemini `1.5-pro` / `1.5-flash` (env-switched) |
| LLM (image) | OpenAI `gpt-image-2` / `dall-e-3` OR Gemini `imagen-3.0-generate-001` |
| Streaming | Server-Sent Events (FastAPI `StreamingResponse`, browser `fetch` reader) |
| External | Facebook Graph API v19.0 |
| Deploy | Railway (backend, `railway.json`), Vercel (frontend), Docker / docker-compose for dev |

Multi-agent orchestration framework (LangGraph, AutoGen, CrewAI): **Not detected from source code.**
ReAct / tool-use loop: **Not detected from source code.**
Vector DB / RAG retrieval: **Not detected from source code.**
Persistent agent memory beyond `Job.style_profile` JSON column: **Not detected from source code.**
