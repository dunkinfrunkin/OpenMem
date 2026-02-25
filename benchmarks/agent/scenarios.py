"""Agent-in-the-loop benchmark scenarios.

Each scenario pre-populates a memory store, then gives an LLM agent
a question to answer using only `memory_recall`.  We measure whether
the agent arrives at the correct answer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from benchmarks.scenarios.scenarios import LinkDef, MemoryDef, OperationDef


@dataclass
class AgentScenario:
    name: str
    description: str
    task: str                      # question the agent must answer
    expected_answer: str           # ground truth for the LLM judge
    key_facts: list[str]           # facts that MUST appear in a correct answer
    memories: list[MemoryDef] = field(default_factory=list)
    links: list[LinkDef] = field(default_factory=list)
    operations: list[OperationDef] = field(default_factory=list)
    requires_graph: bool = False
    requires_contradiction: bool = False
    requires_supersession: bool = False


# ---------------------------------------------------------------------------
# 1. Simple fact retrieval
# ---------------------------------------------------------------------------

def build_fact_retrieval() -> AgentScenario:
    memories = [
        MemoryDef(id="db_engine", text="The project uses SQLite as its database engine"),
        MemoryDef(id="db_wal", text="SQLite is configured in WAL mode for better concurrent read performance"),
        MemoryDef(id="db_fts", text="Full-text search is powered by SQLite FTS5 extension"),
        MemoryDef(id="db_path", text="The default database path is ~/.openmem/memory.db"),
        MemoryDef(id="unrelated_1", text="The frontend uses React with TypeScript for the landing page"),
        MemoryDef(id="unrelated_2", text="CI/CD runs on GitHub Actions with a 5-minute timeout"),
        MemoryDef(id="unrelated_3", text="The team uses Slack for async communication"),
        MemoryDef(id="unrelated_4", text="Code reviews require at least two approvals"),
        MemoryDef(id="unrelated_5", text="Sprint retrospectives happen every two weeks"),
        MemoryDef(id="unrelated_6", text="The logo was designed using Figma"),
    ]
    return AgentScenario(
        name="fact_retrieval",
        description="Simple fact lookup: agent must find specific technical details from memory",
        task="What database engine does the project use and how is it configured? Include the search mode and default path.",
        expected_answer="The project uses SQLite configured in WAL mode with FTS5 for full-text search. The default database path is ~/.openmem/memory.db.",
        key_facts=["SQLite", "WAL mode", "FTS5", "~/.openmem/memory.db"],
        memories=memories,
    )


# ---------------------------------------------------------------------------
# 2. Incident investigation (multi-hop chain)
# ---------------------------------------------------------------------------

def build_incident_investigation() -> AgentScenario:
    memories = [
        MemoryDef(
            id="incident",
            text="Users reported slow page loads on the dashboard, some pages taking over 8 seconds",
            metadata={"type": "incident", "entities": ["dashboard", "performance"]},
        ),
        MemoryDef(
            id="root_cause",
            text="Investigation found the slow dashboard was caused by missing database indexes on the orders table",
            metadata={"entities": ["database", "indexes", "orders"]},
        ),
        MemoryDef(
            id="fix",
            text="Added composite index on (user_id, created_at) to the orders table to fix the slow queries",
            metadata={"entities": ["database", "orders", "index"]},
        ),
        MemoryDef(
            id="result",
            text="After adding the index, dashboard load time improved from 8 seconds to 200 milliseconds",
            metadata={"entities": ["dashboard", "performance"]},
        ),
        MemoryDef(
            id="prevention",
            text="New policy: run EXPLAIN ANALYZE on all new queries before deployment to prevent future performance issues",
            metadata={"type": "decision", "entities": ["database", "deployment"]},
        ),
        # distractors
        MemoryDef(id="d1", text="The payment service uses Stripe API for processing credit cards"),
        MemoryDef(id="d2", text="User authentication is handled via OAuth2 with Google as the identity provider"),
        MemoryDef(id="d3", text="The notification system sends emails through SendGrid"),
        MemoryDef(id="d4", text="API rate limiting is set to 100 requests per minute per user"),
        MemoryDef(id="d5", text="The search feature uses Elasticsearch for product catalog queries"),
        MemoryDef(id="d6", text="Static assets are served from CloudFront CDN"),
        MemoryDef(id="d7", text="The mobile app uses React Native for cross-platform development"),
        MemoryDef(id="d8", text="Database backups run daily at 3 AM UTC"),
    ]

    links = [
        LinkDef(source_id="incident", target_id="root_cause", rel_type="depends_on", weight=0.9),
        LinkDef(source_id="root_cause", target_id="fix", rel_type="supports", weight=0.8),
        LinkDef(source_id="fix", target_id="result", rel_type="supports", weight=0.8),
        LinkDef(source_id="root_cause", target_id="prevention", rel_type="supports", weight=0.7),
    ]

    return AgentScenario(
        name="incident_investigation",
        description="Agent must piece together a full incident story from linked memories",
        task="A user mentioned the dashboard was slow. What happened? Give me the full story: what was the problem, what caused it, how was it fixed, what was the result, and what did we do to prevent it from happening again?",
        expected_answer="Users reported 8-second dashboard load times. The root cause was missing database indexes on the orders table. The fix was adding a composite index on (user_id, created_at). After the fix, load times dropped to 200ms. To prevent recurrence, a new policy requires EXPLAIN ANALYZE on all queries before deployment.",
        key_facts=[
            "8 seconds",
            "missing indexes",
            "orders table",
            "composite index",
            "user_id, created_at",
            "200 milliseconds",
            "EXPLAIN ANALYZE",
        ],
        memories=memories,
        links=links,
        requires_graph=True,
    )


# ---------------------------------------------------------------------------
# 3. Conflicting information resolution
# ---------------------------------------------------------------------------

def build_conflicting_info() -> AgentScenario:
    memories = [
        MemoryDef(
            id="rest_api",
            text="The API uses REST with JSON responses. All endpoints follow RESTful conventions.",
            metadata={"type": "decision", "confidence": 0.95, "entities": ["API", "REST"]},
        ),
        MemoryDef(
            id="graphql_api",
            text="The API uses GraphQL for all endpoints with a single /graphql route.",
            metadata={"type": "decision", "confidence": 0.4, "entities": ["API", "GraphQL"]},
        ),
        MemoryDef(
            id="postgres_db",
            text="Production database is PostgreSQL 15 running on AWS RDS.",
            metadata={"type": "fact", "confidence": 0.9, "entities": ["PostgreSQL", "database"]},
        ),
        MemoryDef(
            id="mysql_db",
            text="Production database is MySQL 8 hosted on the team's own servers.",
            metadata={"type": "fact", "confidence": 0.3, "entities": ["MySQL", "database"]},
        ),
        MemoryDef(id="d1", text="The frontend communicates with the backend over HTTPS"),
        MemoryDef(id="d2", text="API authentication uses JWT tokens with 1-hour expiry"),
        MemoryDef(id="d3", text="The staging environment mirrors production configuration"),
    ]

    operations = [
        OperationDef(op="contradict", args={"id_a": "rest_api", "id_b": "graphql_api"}),
        OperationDef(op="contradict", args={"id_a": "postgres_db", "id_b": "mysql_db"}),
    ]

    return AgentScenario(
        name="conflicting_info",
        description="Agent must identify and resolve contradictory information in memory",
        task="What API protocol does our service use, and what database runs in production? Be specific.",
        expected_answer="The API uses REST with JSON responses. The production database is PostgreSQL 15 on AWS RDS.",
        key_facts=["REST", "JSON", "PostgreSQL 15"],
        memories=memories,
        operations=operations,
        requires_contradiction=True,
    )


# ---------------------------------------------------------------------------
# 4. Outdated vs current information
# ---------------------------------------------------------------------------

def build_outdated_vs_current() -> AgentScenario:
    memories = [
        MemoryDef(
            id="old_python",
            text="The project requires Python 3.8 or higher",
            metadata={"entities": ["Python"], "age_days": 180},
        ),
        MemoryDef(
            id="new_python",
            text="The project has been upgraded to require Python 3.12 minimum",
            metadata={"entities": ["Python"], "age_days": 0},
        ),
        MemoryDef(
            id="old_framework",
            text="The backend is built with Flask 2.0",
            metadata={"entities": ["Flask"], "age_days": 120},
        ),
        MemoryDef(
            id="new_framework",
            text="The backend has been migrated from Flask to FastAPI for better async support",
            metadata={"entities": ["FastAPI"], "age_days": 0},
        ),
        MemoryDef(
            id="old_deploy",
            text="We deploy to production using manual SSH and rsync",
            metadata={"entities": ["deployment"], "age_days": 90},
        ),
        MemoryDef(
            id="new_deploy",
            text="We deploy to production using automated GitHub Actions CI/CD pipeline",
            metadata={"entities": ["deployment"], "age_days": 0},
        ),
        MemoryDef(id="d1", text="The team follows trunk-based development with short-lived feature branches"),
        MemoryDef(id="d2", text="Code style is enforced by ruff linter with default configuration"),
        MemoryDef(id="d3", text="Documentation is hosted on GitHub Pages using MkDocs"),
    ]

    operations = [
        OperationDef(op="supersede", args={"old_id": "old_python", "new_id": "new_python"}),
        OperationDef(op="supersede", args={"old_id": "old_framework", "new_id": "new_framework"}),
        OperationDef(op="supersede", args={"old_id": "old_deploy", "new_id": "new_deploy"}),
    ]

    return AgentScenario(
        name="outdated_vs_current",
        description="Agent must identify current state despite outdated memories being present",
        task="What are the current technical requirements? Specifically: what Python version, what web framework, and how do we deploy?",
        expected_answer="Python 3.12 minimum, FastAPI for the backend, and deployment via GitHub Actions CI/CD.",
        key_facts=["Python 3.12", "FastAPI", "GitHub Actions"],
        memories=memories,
        operations=operations,
        requires_supersession=True,
    )


# ---------------------------------------------------------------------------
# 5. Cross-topic synthesis
# ---------------------------------------------------------------------------

def build_cross_topic_synthesis() -> AgentScenario:
    memories = [
        # Security memories
        MemoryDef(id="sec_1", text="All API endpoints require HTTPS; HTTP requests are rejected"),
        MemoryDef(id="sec_2", text="API keys and secrets must be stored in environment variables, never committed to source code"),
        MemoryDef(id="sec_3", text="Rate limiting is set to 200 requests per minute per API key"),
        MemoryDef(id="sec_4", text="SQL injection is prevented by using parameterized queries throughout the codebase"),
        MemoryDef(id="sec_5", text="CORS is configured to only allow requests from app.example.com and admin.example.com"),
        # Deployment memories
        MemoryDef(id="dep_1", text="Production deployments use blue-green strategy with automatic rollback on health check failure"),
        MemoryDef(id="dep_2", text="Docker images are built in CI and pushed to ECR before deployment"),
        MemoryDef(id="dep_3", text="Kubernetes manages container orchestration with auto-scaling from 2 to 20 pods"),
        MemoryDef(id="dep_4", text="Canary releases expose new versions to 5% of traffic before full rollout"),
        MemoryDef(id="dep_5", text="All deployments require passing security scan with Trivy before promotion"),
        # Unrelated
        MemoryDef(id="d1", text="The team standup is at 10 AM EST every weekday"),
        MemoryDef(id="d2", text="Design mockups are created in Figma and reviewed in weekly design syncs"),
        MemoryDef(id="d3", text="The product roadmap is tracked in Linear with quarterly OKRs"),
        MemoryDef(id="d4", text="New engineers go through a 2-week onboarding program"),
        MemoryDef(id="d5", text="The analytics pipeline uses Apache Kafka for event streaming"),
    ]

    return AgentScenario(
        name="cross_topic_synthesis",
        description="Agent must search across multiple topics and synthesize a coherent answer",
        task="Describe the security measures in our deployment pipeline. How do we ensure that deployments are secure?",
        expected_answer="Deployments are secured through multiple layers: HTTPS enforcement, secrets stored in env vars (not source code), Docker images scanned with Trivy before promotion, blue-green deployments with automatic rollback, CORS restricted to specific domains, rate limiting at 200 req/min, and parameterized queries to prevent SQL injection.",
        key_facts=[
            "HTTPS",
            "environment variables",
            "Trivy",
            "blue-green",
            "CORS",
            "rate limiting",
        ],
        memories=memories,
    )


# ---------------------------------------------------------------------------
# 6. Needle in haystack (agent version)
# ---------------------------------------------------------------------------

def build_needle_retrieval() -> AgentScenario:
    memories = [
        MemoryDef(
            id="needle",
            text="The database connection pool is configured with max_connections=25 and connection_timeout=30 seconds in production",
        ),
    ]
    # 80 distractors across different domains
    topics = [
        ("onboarding", "The {} onboarding step {} covers {} procedures for new team members"),
        ("compliance", "Compliance requirement {} mandates {} review for {} documentation"),
        ("facilities", "The {} office facility {} has {} available for team use"),
        ("hr", "HR policy {} defines the {} process for {} situations"),
    ]
    idx = 0
    fillers = ["first", "second", "third", "quarterly", "annual", "weekly", "monthly", "standard"]
    areas = ["general", "technical", "administrative", "operational", "financial", "legal", "safety", "quality"]
    for topic_name, template in topics:
        for i in range(20):
            memories.append(MemoryDef(
                id=f"hay_{idx}",
                text=template.format(fillers[i % len(fillers)], i + 1, areas[i % len(areas)]),
            ))
            idx += 1

    return AgentScenario(
        name="needle_retrieval",
        description="Agent must find one specific technical fact buried among 80 unrelated memories",
        task="What are the database connection pool settings in production? I need the exact numbers.",
        expected_answer="max_connections=25 and connection_timeout=30 seconds",
        key_facts=["25", "30 seconds"],
        memories=memories,
    )


# ---------------------------------------------------------------------------
# 7. Multi-query reasoning
# ---------------------------------------------------------------------------

def build_multi_query_reasoning() -> AgentScenario:
    memories = [
        MemoryDef(id="arch_1", text="The system follows a microservices architecture with 6 services"),
        MemoryDef(id="arch_2", text="Inter-service communication uses gRPC with protocol buffers"),
        MemoryDef(id="arch_3", text="The API gateway is implemented with Kong and handles routing, auth, and rate limiting"),
        MemoryDef(id="auth_1", text="User authentication uses OAuth2 with Google and GitHub as identity providers"),
        MemoryDef(id="auth_2", text="JWT tokens are issued with 1-hour expiry and refresh tokens last 30 days"),
        MemoryDef(id="auth_3", text="Service-to-service auth uses mutual TLS with certificates rotated every 90 days"),
        MemoryDef(id="data_1", text="User data is stored in PostgreSQL with row-level security policies"),
        MemoryDef(id="data_2", text="Session data is cached in Redis with a 24-hour TTL"),
        MemoryDef(id="data_3", text="File uploads go to S3 with server-side encryption using AES-256"),
        MemoryDef(id="monitor_1", text="Application metrics are collected by Prometheus and visualized in Grafana"),
        MemoryDef(id="monitor_2", text="Distributed tracing uses OpenTelemetry with Jaeger as the backend"),
        MemoryDef(id="monitor_3", text="Alerts are sent to PagerDuty for P1 incidents and to Slack for P2-P4"),
        # distractors
        MemoryDef(id="d1", text="The company was founded in 2019 in San Francisco"),
        MemoryDef(id="d2", text="The marketing team uses HubSpot for campaign management"),
        MemoryDef(id="d3", text="Board meetings happen quarterly with investor updates"),
    ]

    return AgentScenario(
        name="multi_query_reasoning",
        description="Agent must make multiple searches across different topics to build a complete picture",
        task="Give me a complete overview of how authentication and authorization work in our system. Cover user auth, service-to-service auth, and how tokens are managed.",
        expected_answer="User authentication uses OAuth2 with Google/GitHub as identity providers. JWT tokens are issued with 1-hour expiry and 30-day refresh tokens. Service-to-service communication is secured with mutual TLS, certificates rotated every 90 days. The API gateway (Kong) handles auth enforcement and rate limiting.",
        key_facts=[
            "OAuth2",
            "Google",
            "GitHub",
            "JWT",
            "1-hour",
            "30 days",
            "mutual TLS",
            "90 days",
        ],
        memories=memories,
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def all_agent_scenarios() -> list[AgentScenario]:
    return [
        build_fact_retrieval(),
        build_incident_investigation(),
        build_conflicting_info(),
        build_outdated_vs_current(),
        build_cross_topic_synthesis(),
        build_needle_retrieval(),
        build_multi_query_reasoning(),
    ]
