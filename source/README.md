<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=2,14,28,42&height=220&section=header&text=SYNAPSEFORGE&fontSize=56&fontAlignY=38&desc=Autonomous%20Multi-Modal%20AI%20Generative%20Engine%20%26%20Traffic%20Bandit%20Matrix&descAlignY=62&descSize=17" alt="SynapseForge Banner" width="100%"/>
</p>

<p align="center">
  <a href="#-architecture-topology"><img src="https://img.shields.io/badge/Architecture-Distributed%20Micro--Engine-6366f1?style=for-the-badge&logo=diagramsdotnet&logoColor=white" alt="Architecture" /></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/Runtime-PHP%207.4%2B%20%7C%208.x-777bb4?style=for-the-badge&logo=php&logoColor=white" alt="PHP Runtime" /></a>
  <a href="#-data-persistence-philosophy"><img src="https://img.shields.io/badge/Storage-Zero--Config%20SQLite-003b57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" /></a>
  <a href="#-neural-synthesis-matrix"><img src="https://img.shields.io/badge/AI%20Core-Venice%20Diffusion%20%26%20Video-ff0055?style=for-the-badge&logo=openai&logoColor=white" alt="AI Core" /></a>
  <a href="#-multi-armed-bandit-conversion-engine"><img src="https://img.shields.io/badge/Optimization-Adaptive%20Bandit%20Splitter-10b981?style=for-the-badge&logo=googleanalytics&logoColor=white" alt="Bandit Engine" /></a>
  <a href="#-omnichannel-capi-telemetry"><img src="https://img.shields.io/badge/Tracking-Multi--Platform%20CAPI-0284c7?style=for-the-badge&logo=meta&logoColor=white" alt="CAPI" /></a>
</p>

---

## ⚡ Executive Summary

**SynapseForge** is an enterprise-grade, high-throughput autonomous backend engine purpose-built for generative AI media platforms and conversion-optimized web applications. 

Unlike traditional monolithic frameworks that introduce bloat and heavy ORM overhead, SynapseForge operates on a **zero-dependency, asynchronous execution architecture**. It unifies state-of-the-art multi-modal neural generation (synchronous 4K diffusion and asynchronous prompt-to-video / img2vid polling queues) with an algorithmic multi-armed bandit traffic distributor, direct server-side Conversion APIs (CAPI), privacy-preserving zero-cookie analytics, and an autonomous zero-migration SQLite data fabric.

```
       [ Client / Browser / Mobile App ]
                       │
                       ▼
 ╔═════════════════════════════════════════════════════════════════════════╗
 ║                         SYNAPSEFORGE CORE                               ║
 ║                                                                         ║
 ║  ┌───────────────────────────────────────────────────────────────────┐  ║
 ║  │                   Ingress & Anti-Bot Defense                      │  ║
 ║  │      • Invisible Proof-of-Work (nv_pow)    • hCaptcha Shield      │  ║
 ║  └─────────────────────────────────┬─────────────────────────────────┘  ║
 ║                                    │                                    ║
 ║  ┌─────────────────────────────────┴─────────────────────────────────┐  ║
 ║  │               Identity, Auth & Micro-Credits Matrix               │  ║
 ║  │   • Google OAuth 2.0   • X (Twitter) PKCE   • Session Tokens      │  ║
 ║  │   • Device Fingerprint • Resend Email Codes • Credit Deductions   │  ║
 ║  └───────────┬─────────────────────┬─────────────────────┬───────────┘  ║
 ║              │                     │                     │              ║
 ║              ▼                     ▼                     ▼              ║
 ║   ┌─────────────────────┐┌───────────────────┐┌─────────────────────┐   ║
 ║   │   Neural Engine     ││   Bandit Router   ││ Telemetry & CAPI    │   ║
 ║   │ • Synchronous Photo ││ • 13+ LP Variants ││ • Salted IP Tracker │   ║
 ║   │ • Async Video Queue ││ • Dynamic Weights ││ • Meta/X/Reddit CAPI│   ║
 ║   │ • Venice AI Client  ││ • Real-time Splits││ • Telegram Helpdesk │   ║
 ║   └──────────┬──────────┘└─────────┬─────────┘└──────────┬──────────┘   ║
 ║              │                     │                     │              ║
 ║              └─────────────────────┼─────────────────────┘              ║
 ║                                    ▼                                    ║
 ║  ┌───────────────────────────────────────────────────────────────────┐  ║
 ║  │                 Autonomous SQLite Micro-Stores                    │  ║
 ║  │   • Self-provisioning schemas on first hit (CREATE IF NOT EXISTS) │  ║
 ║  └───────────────────────────────────────────────────────────────────┘  ║
 ╚═════════════════════════════════════════════════════════════════════════╝
```

---

## 🏛️ Architecture Topology

### High-Level System Workflow

```mermaid
flowchart TD
    subgraph Client_Layer ["Client & Ingress Layer"]
        User["Client Browser / Mobile App"]
        PoW["Anti-Bot Proof-of-Work & Captcha Gate"]
        User -->|1. Request| PoW
    end

    subgraph Auth_Control ["Auth & Session Controller"]
        AuthRouter{"Auth Method"}
        GoogleOAuth["Google OAuth 2.0"]
        XOAuth["X / Twitter OAuth 2.0"]
        EmailPass["Email + Argon2 / Password"]
        SessionMgr["Session & Credit Allocator"]
        
        PoW -->|2. Verified Ingress| AuthRouter
        AuthRouter -->|Federated| GoogleOAuth
        AuthRouter -->|Federated| XOAuth
        AuthRouter -->|Direct| EmailPass
        GoogleOAuth --> SessionMgr
        XOAuth --> SessionMgr
        EmailPass --> SessionMgr
    end

    subgraph Neural_Pipeline ["Neural Synthesis Engine"]
        GenReq["Generation Ingress (api/generate_request.php)"]
        CreditCheck{"Has Balance?"}
        SyncPhoto["Venice AI Client (Synchronous 4K Photo)"]
        AsyncVideo["Async Video Job Queue"]
        PollStatus["Status Poller (api/generation_status.php)"]

        SessionMgr -->|3. Invoke AI Task| GenReq
        GenReq --> CreditCheck
        CreditCheck -->|Yes - Image| SyncPhoto
        CreditCheck -->|Yes - Video| AsyncVideo
        AsyncVideo -.->|4. Poll Loop| PollStatus
    end

    subgraph Optimization_Layer ["Conversion Optimization & Telemetry"]
        BanditEngine["Multi-Armed Bandit Traffic Splitter"]
        AnalyticsCollector["First-Party Telemetry (a/collect.php)"]
        CAPIRelay["Server-Side CAPI Relays (Meta, X, Reddit, Pinterest)"]
        TelegramBridge["Support Chat to Telegram Bridge"]

        User -->|Traffic Route| BanditEngine
        User -->|Telemetry Events| AnalyticsCollector
        AnalyticsCollector --> CAPIRelay
        User -->|Support Widget| TelegramBridge
    end

    subgraph Storage_Layer ["Zero-Migration Persistence (data/*.sqlite)"]
        AuthDB[("auth.sqlite")]
        BanditDB[("bandit.sqlite")]
        AnalyticsDB[("analytics.sqlite")]
        ChatDB[("chat.sqlite")]

        SessionMgr --> AuthDB
        BanditEngine --> BanditDB
        AnalyticsCollector --> AnalyticsDB
        TelegramBridge --> ChatDB
    end

    classDef primary fill:#6366f1,stroke:#4338ca,stroke-width:2px,color:#fff;
    classDef success fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;
    classDef warning fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;
    classDef danger fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff;

    class GenReq,SyncPhoto,AsyncVideo primary;
    class BanditEngine,AnalyticsCollector,CAPIRelay success;
    class SessionMgr,GoogleOAuth,XOAuth warning;
    class AuthDB,BanditDB,AnalyticsDB,ChatDB danger;
```

---

## 🔬 Core Subsystems Deep Dive

### 1. 🧠 Multi-Modal Neural Synthesis Matrix (`api/`, `venice_client.php`)
- **Dual Pipeline Inference:**
  - **Synchronous Photorealistic Diffusion:** Sub-second generation and response delivery for text-to-image requests via external Venice AI inference models.
  - **Asynchronous Prompt-to-Video & Img2Vid Queue:** High-complexity video synthesis tasks are scheduled asynchronously into a polling queue. Clients receive immediate job tokens and poll `api/generation_status.php` with progressive exponential backoff until render completion.
- **Fail-Safe Credit Accounting:** Credits are held in escrow during generation and only deducted upon guaranteed stream/file return.

```mermaid
sequenceDiagram
    autonumber
    actor Client as User / Dashboard
    participant API as api/generate_request.php
    participant DB as SQLite Credit Ledger
    participant Venice as Venice AI Inference Cluster
    participant Status as api/generation_status.php

    Client->>API: POST /api/generate_request.php (prompt, mode: video/photo)
    API->>DB: Verify & hold credit balance
    alt Photo Mode (Synchronous)
        API->>Venice: Dispatch generation payload
        Venice-->>API: 200 OK + Raw Image URL
        API->>DB: Finalize credit debit
        API-->>Client: Return rendered asset URI
    else Video / Motion Mode (Asynchronous)
        API->>Venice: Queue rendering job
        Venice-->>API: 202 Accepted + Job Queue ID
        API-->>Client: Return { status: "queued", job_id: "vn_79a..." }
        loop Status Polling
            Client->>Status: GET /api/generation_status.php?job_id=vn_79a...
            Status->>Venice: Query upstream task state
            Venice-->>Status: In Progress / Render Complete
            Status-->>Client: Current progress / Final asset payload
        end
        Status->>DB: Deduct credits on successful completion
    end
```

### 2. ⚖️ Multi-Armed Bandit Dynamic Traffic Router (`lp/lp_ab.php`, `api/bandit.php`)
- **Autonomous Variant Routing:** Intelligently balances traffic allocation across up to 13 landing page variants (`v1`–`v13`) based on real-time server-side conversion feedback.
- **Dynamic Weight Adaptation:** Uses Bayesian conversion tracking logged in `split_weight_log` to shift traffic towards winning variants while maintaining exploration across new challenger layouts.
- **Persistent Attribution:** Issues tamper-proof server-side session cookies to guarantee visitor consistency across multi-step funnels.

### 3. 🛡️ Zero-Trust Identity, Authentication & Micro-Credits (`auth/`, `functions/auth_db.php`)
- **Federated & Direct Authentication:**
  - **Google OAuth 2.0:** Secure identity token verification and one-click account creation.
  - **X (Twitter) OAuth 2.0 with PKCE:** Modern OAuth flow for social authentication without client secrets exposed.
  - **Password Auth:** Cryptographically secure password hashing with automated salting.
- **Resend Universal Email Verification:** Purpose-based rate-limited transactional codes (`functions/email_codes.php`) with attempt counters and expiry windows.
- **Device & Fingerprint Binding:** Guards against credential stuffing and session theft by validating IP subnet and user agent signatures.

### 4. 📊 First-Party Privacy-Preserving Telemetry (`a/collect.php`)
- **Cookieless Analytics:** Self-hosted event ingestion pipeline capturing clicks, views, scroll depths, and conversion milestones.
- **GDPR-Compliant Salted Hashing:** User IP addresses are immediately hashed using a secret rotating salt (`LXTRACK_IP_SALT`) before persistence—zero raw IP addresses or personally identifiable network telemetry is ever stored.
- **Real-Time Country & Geo Lookups:** Resolves geographical distributions through local lightweight IP range lookups.

### 5. 📡 Omnichannel Server-Side Conversion API (CAPI) (`functions/*_capi.php`)
- **Bypasses Ad-Blockers & Safari ITP:** Client-side tracking pixels are prone to 40%+ signal loss. SynapseForge routes conversion events server-to-server:
  - **Meta Conversions API (CAPI)**
  - **X (Twitter) CAPI**
  - **Reddit CAPI**
  - **Pinterest CAPI**
- **Deduplication Engine:** Synchronizes client-side event IDs with server-side payload hashes to prevent double counting.

### 6. 💬 Telegram Bridge Support Gateway (`chat/`, `functions/support_lib.php`)
- **Bi-Directional Helpdesk:** Visitor messages submitted to the front-end chat widget are instantly pushed to a dedicated Telegram admin chat via Telegram Bot webhook APIs.
- **Agent Replies Delivered to Web:** Admin responses typed inside Telegram are automatically polled back and rendered in the visitor's browser in real-time.

### 7. 📦 Desktop Binary Distribution Gateway (`api/desktop_download.php`, `api/dl_track.php`)
- **OS-Aware Download Routing:** Auto-detects client architecture (Windows x64 / macOS Apple Silicon / macOS Intel) and provides signed, rate-limited direct download streams with telemetry tracking.

---

## 📁 Repository Anatomy

```text
source/
├── api/                        # REST API Endpoints
│   ├── auth_google.php         # Google OAuth 2.0 token exchange & callback
│   ├── auth_x.php              # X (Twitter) PKCE OAuth integration
│   ├── bandit.php              # Multi-armed bandit split testing controller
│   ├── desktop_download.php    # Signed OS binary download distributor
│   ├── dl_track.php            # Download telemetric tracker
│   ├── generate_request.php    # AI photo/video dispatch endpoint
│   ├── generation_status.php   # Async video generation polling worker
│   ├── nv_notify.php           # Event notification distributor
│   ├── nv_pow.php              # Invisible client proof-of-work challenge
│   └── venice_client.php       # Low-latency Venice AI client wrapper
├── auth/                       # OAuth callback handlers & access controllers
├── auth_callback.php           # Central OAuth redirect orchestrator
├── chat/                       # Live visitor chat widget backend
│   ├── chat_api.php            # Chat polling & message ingestion
│   └── upload_resume.php       # Careers & resume attachment handler
├── data/                       # Storage & Scheduled Jobs
│   ├── desktop_links.json      # Binary distribution metadata targets
│   ├── batch_send.php          # Async campaign email runner
│   ├── send_campaign.php       # Scheduled campaign push worker
│   └── ios_send.php            # Push notification delivery worker
├── functions/                  # Core Business Logic & Helpers
│   ├── auth_db.php             # User model, credentials & session state
│   ├── email_codes.php         # Universal verification code engine
│   ├── welcome_mail.php        # Transactional Resend email dispatcher
│   ├── support_lib.php         # Telegram Bot bi-directional bridge
│   ├── captcha.php             # hCaptcha server-side verification
│   ├── reviews.php             # Product reviews and rating aggregation
│   ├── x_capi.php              # Server-to-server X (Twitter) CAPI
│   └── phone_verify.php        # SMS verification engine
├── lk/                         # Member Dashboard (Личный Кабинет) Engine
│   ├── lk_core.php             # Member session guard & credit status
│   └── lk_dlblock.php          # Dynamic download portal widgets
├── a/                          # Self-Hosted Analytics Engine
│   ├── collect.php             # Salted event collector endpoint
│   └── dashboard.php           # Internal conversion & telemetry dashboard
├── PHPMailer/                  # Vendored SMTP transport library
├── .env.example                # Blueprint for environment variables
├── ENGINE.md                   # Technical subsystem execution specifications
└── LICENSE                     # Proprietary software license
```

---

## 🛠️ API Interface Specifications

| Endpoint | Method | Purpose | Key Parameters |
|:---|:---:|:---|:---|
| `/api/generate_request.php` | `POST` | Dispatches neural generation request | `prompt`, `aspect_ratio`, `mode` (`photo` \| `video`) |
| `/api/generation_status.php` | `GET` | Polls status of async generation job | `job_id`, `token` |
| `/api/bandit.php` | `GET` | Fetches active variant for visitor | `cid`, `lp_version` |
| `/a/collect.php` | `POST` | Ingests privacy-first click/conversion event | `event`, `target`, `variant`, `timestamp` |
| `/api/auth_google.php` | `POST` | Validates Google OAuth credential token | `credential` |
| `/api/auth_x.php` | `GET` | Handles X OAuth callback & code exchange | `code`, `state` |
| `/api/desktop_download.php` | `GET` | Delivers signed OS installation binary | `os` (`win` \| `mac`), `version` |

---

## 💾 Zero-Migration Data Persistence

SynapseForge removes the fragility of database migrations. Every subsystem utilizes an autonomous, isolated SQLite database under `data/`:

* **`data/users.sqlite`** — User credentials, salted password hashes, credit balances, activation codes.
* **`data/bandit.sqlite`** — Variant impressions, click counts, conversion attributions.
* **`data/analytics.sqlite`** — Anonymized click streams, geographical buckets, event timestamps.
* **`data/chat.sqlite`** — Visitor sessions, Telegram message mappings, resolution states.

> **Zero-Setup Schema Ingestion:** Every database module automatically runs `CREATE TABLE IF NOT EXISTS` upon its first connection. Creating a new local or staging environment requires zero SQL seed scripts or database configuration.

---

## 🚀 Quickstart & Development

### Prerequisites
* **PHP 7.4+** or **PHP 8.1+** (CLI or FPM) with `php-curl`, `php-sqlite3`, and `php-json` extensions enabled.
* No Composer or Node.js build steps required.

### 1. Clone & Configure Environment
```bash
# Clone the repository
git clone https://github.com/dk5488/SynapseForge.git
cd SynapseForge

# Instantiate environment variables from template
cp .env.example .env
```

### 2. Configure Key Parameters in `.env`
Edit `.env` with your preferred credentials:
```ini
# Venice AI Inference Engine
VENICE_API_KEY=your_venice_api_key

# Privacy Telemetry Salt
LXTRACK_IP_SALT=c8f2b3149e0a78619bc...

# Telegram Bridge
TG_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TG_CHAT_ID=-100123456789

# Resend Transactional Mail
RESEND_API_KEY=re_123456789...
```

### 3. Launch Development Server
```bash
php -S 127.0.0.1:8000
```
Visit `http://127.0.0.1:8000/api/bandit.php` in your browser to verify that the SQLite databases initialize automatically under `data/`.

---

## 🔒 Security & Data Governance

1. **Strict Secrets Redaction:** Credentials and API keys are read exclusively from environment variables (`$_ENV` or process environment). Hardcoded secret fallbacks have been eliminated.
2. **GDPR/CCPA Compliance:** Raw IP addresses are never saved to disk. All network addresses are hashed with high-entropy cryptographic salt before persistence.
3. **Bot & DDoS Mitigation:** High-value generation and trial endpoints are guarded with invisible proof-of-work challenges (`api/nv_pow.php`) and server-side hCaptcha validation.
4. **Isolated Blast Radius:** Each subsystem writes to its own isolated SQLite database, preventing a failure in analytics from cascading to identity or neural generation.

---

<p align="center">
  <b>SynapseForge</b> • Engineered for high-velocity AI generation and autonomous conversion optimization.
</p>
