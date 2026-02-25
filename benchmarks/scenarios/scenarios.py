from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemoryDef:
    id: str
    text: str
    metadata: dict | None = None


@dataclass
class LinkDef:
    source_id: str
    target_id: str
    rel_type: str = "mentions"
    weight: float = 0.5


@dataclass
class OperationDef:
    op: str  # "supersede" | "contradict" | "reinforce"
    args: dict = field(default_factory=dict)


@dataclass
class QueryDef:
    query: str
    relevant_ids: list[str] = field(default_factory=list)
    relevance_grades: dict[str, int] | None = None
    top_k: int = 10


@dataclass
class Scenario:
    name: str
    description: str
    requires_graph: bool = False
    requires_contradiction: bool = False
    requires_supersession: bool = False
    memories: list[MemoryDef] = field(default_factory=list)
    links: list[LinkDef] = field(default_factory=list)
    operations: list[OperationDef] = field(default_factory=list)
    queries: list[QueryDef] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scenario 1: Basic Recall -- 50 memories across 5 topics
# ---------------------------------------------------------------------------


def build_basic_recall() -> Scenario:
    memories = []

    python_texts = [
        "Python uses indentation for code blocks instead of curly braces",
        "List comprehensions in Python provide a concise way to create lists",
        "Python's GIL limits true parallelism in CPU-bound threads",
        "The asyncio module enables asynchronous programming in Python",
        "Python decorators use the @ syntax to modify function behavior",
        "Type hints in Python are checked by mypy but not enforced at runtime",
        "Virtual environments isolate Python project dependencies",
        "Python's dataclasses module reduces boilerplate for data containers",
        "The walrus operator := allows assignment within expressions in Python",
        "Python supports multiple inheritance through the MRO algorithm",
    ]
    for i, text in enumerate(python_texts):
        memories.append(MemoryDef(id=f"py_{i}", text=text, metadata={"entities": ["Python"]}))

    db_texts = [
        "SQLite stores the entire database in a single file on disk",
        "PostgreSQL supports JSONB columns for semi-structured data",
        "Database indexes speed up queries but slow down writes",
        "ACID transactions ensure data integrity in relational databases",
        "Connection pooling reduces database connection overhead",
        "Database migrations track schema changes in version control",
        "The N+1 query problem occurs when fetching related records in loops",
        "SQLite uses WAL mode for better concurrent read performance",
        "Foreign keys enforce referential integrity between database tables",
        "Full-text search indexes enable fast keyword queries on text columns",
    ]
    for i, text in enumerate(db_texts):
        memories.append(MemoryDef(id=f"db_{i}", text=text, metadata={"entities": ["database"]}))

    test_texts = [
        "Unit tests verify individual functions in isolation from dependencies",
        "Integration tests check that components work together correctly",
        "Pytest fixtures provide reusable test setup and teardown logic",
        "Test coverage measures the percentage of code exercised by tests",
        "Mocking replaces real dependencies with controlled fake objects in tests",
        "Property-based testing generates random inputs to find edge cases",
        "Test-driven development writes tests before implementing the code",
        "Continuous integration runs tests automatically on every commit",
        "Snapshot testing compares output against a stored reference",
        "Load testing measures application performance under heavy traffic",
    ]
    for i, text in enumerate(test_texts):
        memories.append(MemoryDef(id=f"test_{i}", text=text, metadata={"entities": ["testing"]}))

    deploy_texts = [
        "Docker containers package applications with all their dependencies",
        "Kubernetes orchestrates container deployment and scaling",
        "Blue-green deployments reduce downtime during releases",
        "CI/CD pipelines automate building, testing, and deploying code",
        "Environment variables configure applications without code changes",
        "Health checks monitor whether deployed services are running correctly",
        "Rolling deployments gradually replace old instances with new ones",
        "Infrastructure as code defines server setup in version-controlled files",
        "Canary releases expose new versions to a small percentage of traffic first",
        "Reverse proxies like Nginx route incoming traffic to backend services",
    ]
    for i, text in enumerate(deploy_texts):
        memories.append(
            MemoryDef(id=f"deploy_{i}", text=text, metadata={"entities": ["deployment"]})
        )

    sec_texts = [
        "SQL injection attacks exploit unvalidated input in database queries",
        "HTTPS encrypts data in transit between client and server",
        "CORS headers control which domains can make cross-origin requests",
        "JWT tokens encode authentication claims in a signed JSON payload",
        "Rate limiting prevents abuse by capping requests per time window",
        "Content Security Policy headers mitigate cross-site scripting attacks",
        "OAuth2 delegates authentication to trusted identity providers",
        "Password hashing with bcrypt protects stored credentials",
        "Two-factor authentication adds a second verification step beyond passwords",
        "API keys should be stored in environment variables, never in source code",
    ]
    for i, text in enumerate(sec_texts):
        memories.append(MemoryDef(id=f"sec_{i}", text=text, metadata={"entities": ["security"]}))

    queries = [
        QueryDef(
            query="How does Python handle concurrency and parallelism?",
            relevant_ids=["py_2", "py_3"],
            relevance_grades={"py_2": 3, "py_3": 3, "py_0": 1},
        ),
        QueryDef(
            query="What database indexing strategies improve query performance?",
            relevant_ids=["db_2", "db_9", "db_7"],
            relevance_grades={"db_2": 3, "db_9": 3, "db_7": 2},
        ),
        QueryDef(
            query="How do you write effective automated tests?",
            relevant_ids=["test_0", "test_1", "test_2", "test_4", "test_6"],
            relevance_grades={
                "test_0": 3,
                "test_1": 2,
                "test_2": 2,
                "test_4": 2,
                "test_6": 2,
            },
        ),
        QueryDef(
            query="What are best practices for zero-downtime deployments?",
            relevant_ids=["deploy_2", "deploy_6", "deploy_8"],
            relevance_grades={"deploy_2": 3, "deploy_6": 3, "deploy_8": 2},
        ),
        QueryDef(
            query="How do you prevent common web security vulnerabilities?",
            relevant_ids=["sec_0", "sec_5", "sec_2", "sec_4"],
            relevance_grades={"sec_0": 3, "sec_5": 3, "sec_2": 2, "sec_4": 2},
        ),
    ]

    return Scenario(
        name="basic_recall",
        description="50 memories across 5 topics. Tests basic retrieval quality.",
        memories=memories,
        queries=queries,
    )


# ---------------------------------------------------------------------------
# Scenario 2: Graph-Boosted Recall -- hub-and-spoke knowledge graph
# ---------------------------------------------------------------------------


def build_graph_boosted() -> Scenario:
    memories = [
        MemoryDef(
            id="arch_hub",
            text="We chose a microservices architecture for the payment system",
            metadata={"type": "decision", "entities": ["microservices", "payment"]},
        ),
        MemoryDef(
            id="arch_spoke1",
            text="Each microservice owns its own database schema",
            metadata={"entities": ["microservices"]},
        ),
        MemoryDef(
            id="arch_spoke2",
            text="The team decided on gRPC for inter-service communication",
            metadata={"type": "decision", "entities": ["gRPC"]},
        ),
        MemoryDef(
            id="arch_spoke3",
            text="Circuit breakers prevent cascading failures between components",
            metadata={"entities": ["resilience"]},
        ),
        MemoryDef(
            id="arch_2hop",
            text="Protocol buffers define the message format for all RPCs",
            metadata={"entities": ["protobuf", "gRPC"]},
        ),
        MemoryDef(id="distractor_1", text="The frontend uses React with TypeScript"),
        MemoryDef(id="distractor_2", text="We use GitHub Actions for CI/CD pipelines"),
        MemoryDef(id="distractor_3", text="The team follows two-week sprint cycles"),
        MemoryDef(id="distractor_4", text="Code reviews require at least two approvals"),
        MemoryDef(id="distractor_5", text="Documentation is written in Markdown"),
    ]

    links = [
        LinkDef(source_id="arch_hub", target_id="arch_spoke1", rel_type="supports", weight=0.8),
        LinkDef(source_id="arch_hub", target_id="arch_spoke2", rel_type="supports", weight=0.7),
        LinkDef(source_id="arch_hub", target_id="arch_spoke3", rel_type="supports", weight=0.6),
        LinkDef(
            source_id="arch_spoke2", target_id="arch_2hop", rel_type="depends_on", weight=0.7
        ),
    ]

    queries = [
        QueryDef(
            query="Why did we choose microservices for payments?",
            relevant_ids=["arch_hub", "arch_spoke1", "arch_spoke2", "arch_spoke3"],
            relevance_grades={
                "arch_hub": 3,
                "arch_spoke1": 3,
                "arch_spoke2": 2,
                "arch_spoke3": 2,
                "arch_2hop": 1,
            },
            top_k=5,
        ),
        QueryDef(
            query="How do our services communicate?",
            relevant_ids=["arch_spoke2", "arch_2hop", "arch_hub"],
            relevance_grades={
                "arch_spoke2": 3,
                "arch_2hop": 3,
                "arch_hub": 2,
                "arch_spoke1": 1,
            },
            top_k=5,
        ),
    ]

    return Scenario(
        name="graph_boosted",
        description="Hub-and-spoke knowledge graph. Tests graph traversal for "
        "retrieving connected memories without direct lexical match.",
        requires_graph=True,
        memories=memories,
        links=links,
        queries=queries,
    )


# ---------------------------------------------------------------------------
# Scenario 3: Needle in Haystack
# ---------------------------------------------------------------------------


def build_needle_in_haystack() -> Scenario:
    memories = [
        MemoryDef(
            id="needle",
            text="The database connection timeout is set to 30 seconds in production config",
            metadata={"entities": ["database", "production"]},
        ),
    ]

    domains = ["HR", "logistics", "marketing", "sales", "facilities"]
    actions = ["policy", "process", "guideline", "procedure", "standard"]
    for i in range(100):
        domain = domains[i % len(domains)]
        action = actions[(i // len(domains)) % len(actions)]
        memories.append(
            MemoryDef(
                id=f"hay_{i}",
                text=f"The {domain} {action} for item {i} describes internal "
                f"workflow step {i} regarding {domain} operations",
            )
        )

    queries = [
        QueryDef(
            query="What is the database connection timeout in production?",
            relevant_ids=["needle"],
            relevance_grades={"needle": 3},
            top_k=5,
        ),
    ]

    return Scenario(
        name="needle_in_haystack",
        description="1 precise answer among 100+ distractors. Tests precision at low K.",
        memories=memories,
        queries=queries,
    )


# ---------------------------------------------------------------------------
# Scenario 4: Temporal / Recency
# ---------------------------------------------------------------------------


def build_temporal_recency() -> Scenario:
    memories = [
        MemoryDef(
            id="old_deploy",
            text="We deploy to production using manual SSH and rsync",
            metadata={"entities": ["deployment"], "age_days": 60},
        ),
        MemoryDef(
            id="new_deploy",
            text="We deploy to production using automated GitHub Actions CI/CD",
            metadata={"entities": ["deployment"], "age_days": 0},
        ),
        MemoryDef(
            id="old_python",
            text="The project requires Python 3.8 or higher",
            metadata={"entities": ["Python"], "age_days": 90},
        ),
        MemoryDef(
            id="new_python",
            text="The project has been upgraded to require Python 3.12",
            metadata={"entities": ["Python"], "age_days": 0},
        ),
    ]

    queries = [
        QueryDef(
            query="How do we deploy to production?",
            relevant_ids=["new_deploy", "old_deploy"],
            relevance_grades={"new_deploy": 3, "old_deploy": 1},
        ),
        QueryDef(
            query="What Python version does the project require?",
            relevant_ids=["new_python", "old_python"],
            relevance_grades={"new_python": 3, "old_python": 1},
        ),
    ]

    return Scenario(
        name="temporal_recency",
        description="Old vs. new memories on same topic. Systems with recency bias "
        "should rank newer memories higher.",
        memories=memories,
        queries=queries,
    )


# ---------------------------------------------------------------------------
# Scenario 5: Contradiction Resolution
# ---------------------------------------------------------------------------


def build_contradiction() -> Scenario:
    memories = [
        MemoryDef(
            id="rest_strong",
            text="The API uses REST with JSON responses",
            metadata={"type": "decision", "confidence": 0.95, "entities": ["API", "REST"]},
        ),
        MemoryDef(
            id="graphql_weak",
            text="The API uses GraphQL for all endpoints",
            metadata={"type": "decision", "confidence": 0.4, "entities": ["API", "GraphQL"]},
        ),
        MemoryDef(
            id="postgres_strong",
            text="Production database is PostgreSQL 15",
            metadata={"type": "fact", "confidence": 0.9, "entities": ["PostgreSQL", "database"]},
        ),
        MemoryDef(
            id="mysql_weak",
            text="Production database is MySQL 8",
            metadata={"type": "fact", "confidence": 0.3, "entities": ["MySQL", "database"]},
        ),
    ]

    operations = [
        OperationDef(op="contradict", args={"id_a": "rest_strong", "id_b": "graphql_weak"}),
        OperationDef(op="contradict", args={"id_a": "postgres_strong", "id_b": "mysql_weak"}),
    ]

    queries = [
        QueryDef(
            query="What protocol does our API use?",
            relevant_ids=["rest_strong"],
            relevance_grades={"rest_strong": 3, "graphql_weak": 0},
        ),
        QueryDef(
            query="What database do we use in production?",
            relevant_ids=["postgres_strong"],
            relevance_grades={"postgres_strong": 3, "mysql_weak": 0},
        ),
    ]

    return Scenario(
        name="contradiction",
        description="Contradicting memory pairs with different confidence levels. "
        "Systems with conflict resolution should demote the weaker memory.",
        requires_contradiction=True,
        memories=memories,
        operations=operations,
        queries=queries,
    )


# ---------------------------------------------------------------------------
# Scenario 6: Supersession
# ---------------------------------------------------------------------------


def build_supersession() -> Scenario:
    memories = [
        MemoryDef(
            id="v1_api",
            text="The API is at version 1 with endpoints under /api/v1",
            metadata={"entities": ["API"]},
        ),
        MemoryDef(
            id="v2_api",
            text="The API has been upgraded to version 2 under /api/v2",
            metadata={"entities": ["API"]},
        ),
        MemoryDef(
            id="old_framework",
            text="The backend is built with Flask 2.0",
            metadata={"entities": ["Flask"]},
        ),
        MemoryDef(
            id="new_framework",
            text="The backend has been migrated from Flask to FastAPI",
            metadata={"entities": ["FastAPI"]},
        ),
    ]

    operations = [
        OperationDef(op="supersede", args={"old_id": "v1_api", "new_id": "v2_api"}),
        OperationDef(op="supersede", args={"old_id": "old_framework", "new_id": "new_framework"}),
    ]

    queries = [
        QueryDef(
            query="What version is our API?",
            relevant_ids=["v2_api"],
            relevance_grades={"v2_api": 3, "v1_api": 0},
        ),
        QueryDef(
            query="What framework does the backend use?",
            relevant_ids=["new_framework"],
            relevance_grades={"new_framework": 3, "old_framework": 0},
        ),
    ]

    return Scenario(
        name="supersession",
        description="Old facts superseded by new ones. Systems with supersession "
        "support should penalize old memories.",
        requires_supersession=True,
        memories=memories,
        operations=operations,
        queries=queries,
    )


# ---------------------------------------------------------------------------
# Scenario 7: Multi-Hop Reasoning (causal chain)
# ---------------------------------------------------------------------------


def build_multi_hop() -> Scenario:
    memories = [
        MemoryDef(
            id="bug_report",
            text="Users reported slow page loads on the dashboard",
            metadata={"type": "incident", "entities": ["dashboard", "performance"]},
        ),
        MemoryDef(
            id="root_cause",
            text="The slow queries were caused by missing database indexes",
            metadata={"entities": ["database", "indexes"]},
        ),
        MemoryDef(
            id="fix_applied",
            text="Added composite index on (user_id, created_at) to orders table",
            metadata={"entities": ["database", "orders"]},
        ),
        MemoryDef(
            id="fix_result",
            text="Dashboard load time improved from 8 seconds to 200 milliseconds",
            metadata={"entities": ["dashboard", "performance"]},
        ),
        MemoryDef(
            id="prevention",
            text="We now run EXPLAIN ANALYZE on all new queries before deployment",
            metadata={"type": "decision", "entities": ["database", "deployment"]},
        ),
    ]

    links = [
        LinkDef(source_id="bug_report", target_id="root_cause", rel_type="depends_on", weight=0.9),
        LinkDef(source_id="root_cause", target_id="fix_applied", rel_type="supports", weight=0.8),
        LinkDef(source_id="fix_applied", target_id="fix_result", rel_type="supports", weight=0.8),
        LinkDef(source_id="root_cause", target_id="prevention", rel_type="supports", weight=0.7),
    ]

    queries = [
        QueryDef(
            query="What happened with the slow dashboard?",
            relevant_ids=["bug_report", "root_cause", "fix_applied", "fix_result", "prevention"],
            relevance_grades={
                "bug_report": 3,
                "root_cause": 3,
                "fix_applied": 2,
                "fix_result": 2,
                "prevention": 1,
            },
            top_k=5,
        ),
        QueryDef(
            query="How did we fix the database performance issue?",
            relevant_ids=["root_cause", "fix_applied", "fix_result", "prevention"],
            relevance_grades={
                "root_cause": 3,
                "fix_applied": 3,
                "fix_result": 2,
                "prevention": 2,
                "bug_report": 1,
            },
            top_k=5,
        ),
    ]

    return Scenario(
        name="multi_hop",
        description="Causal chain of linked memories (incident -> cause -> fix -> result). "
        "Graph traversal should retrieve the full chain.",
        requires_graph=True,
        memories=memories,
        links=links,
        queries=queries,
    )


# ---------------------------------------------------------------------------
# Scenario 8: Scale -- latency at different corpus sizes
# ---------------------------------------------------------------------------


def build_scale(corpus_sizes: list[int] | None = None) -> list[Scenario]:
    if corpus_sizes is None:
        corpus_sizes = [100, 500, 1000, 5000]

    topics = [
        "programming",
        "databases",
        "networking",
        "algorithms",
        "operating systems",
        "security",
        "machine learning",
        "web development",
        "mobile development",
        "devops",
    ]

    scenarios = []
    for size in corpus_sizes:
        memories = []
        for i in range(size):
            topic = topics[i % len(topics)]
            memories.append(
                MemoryDef(
                    id=f"scale_{size}_{i}",
                    text=f"Memory {i} about {topic}: This covers concept {i} "
                    f"related to {topic} with details about implementation "
                    f"and best practices for {topic} in production systems",
                    metadata={"entities": [topic]},
                )
            )

        # Fixed query set across sizes for fair comparison
        queries = [
            QueryDef(
                query="What are the best practices for database optimization?",
                relevant_ids=[f"scale_{size}_{i}" for i in range(size) if i % 10 == 1],
                top_k=10,
            ),
            QueryDef(
                query="How does networking work in distributed systems?",
                relevant_ids=[f"scale_{size}_{i}" for i in range(size) if i % 10 == 2],
                top_k=10,
            ),
        ]

        scenarios.append(
            Scenario(
                name=f"scale_{size}",
                description=f"Scale test with {size} memories. Measures latency.",
                memories=memories,
                queries=queries,
            )
        )

    return scenarios


# ---------------------------------------------------------------------------
# Master registry
# ---------------------------------------------------------------------------


def all_scenarios() -> list[Scenario]:
    return [
        build_basic_recall(),
        build_graph_boosted(),
        build_needle_in_haystack(),
        build_temporal_recency(),
        build_contradiction(),
        build_supersession(),
        build_multi_hop(),
        *build_scale(),
    ]
