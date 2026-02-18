import time

from openmem.models import Memory, ScoredMemory
from openmem.scoring import compete, recency_score, strength_score


def test_recency_fresh():
    """A memory accessed just now should have recency near 1.0."""
    now = time.time()
    mem = Memory(text="recent", last_accessed=now, created_at=now - 3600)
    assert abs(recency_score(mem, now) - 1.0) < 0.01


def test_recency_old():
    """A memory not accessed for 30 days should have decayed significantly."""
    now = time.time()
    thirty_days_ago = now - 30 * 86400
    mem = Memory(text="old", last_accessed=thirty_days_ago, created_at=thirty_days_ago)
    r = recency_score(mem, now)
    assert r < 0.3  # exp(-0.05 * 30) ≈ 0.22


def test_recency_uses_created_at_when_never_accessed():
    now = time.time()
    mem = Memory(text="never accessed", created_at=now - 86400, last_accessed=None)
    r = recency_score(mem, now)
    # 1 day old: exp(-0.05 * 1) ≈ 0.95
    assert 0.9 < r < 1.0


def test_strength_fresh():
    now = time.time()
    mem = Memory(text="strong", strength=1.0, access_count=0, created_at=now)
    s = strength_score(mem, now)
    assert abs(s - 1.0) < 0.01


def test_strength_reinforcement():
    """More access should increase strength score."""
    now = time.time()
    mem_low = Memory(text="low", strength=0.5, access_count=0, created_at=now)
    mem_high = Memory(text="high", strength=0.5, access_count=10, created_at=now)
    assert strength_score(mem_high, now) > strength_score(mem_low, now)


def test_strength_clamped():
    """Strength score should never exceed 1.0."""
    now = time.time()
    mem = Memory(text="max", strength=1.0, access_count=100, created_at=now)
    assert strength_score(mem, now) <= 1.0


def test_compete_ranking():
    """Higher activation + recency should rank higher."""
    now = time.time()
    m1 = Memory(id="m1", text="best match", strength=1.0, confidence=1.0,
                created_at=now, last_accessed=now)
    m2 = Memory(id="m2", text="okay match", strength=0.5, confidence=0.5,
                created_at=now - 86400 * 10, last_accessed=now - 86400 * 10)

    activations = {"m1": 1.0, "m2": 0.3}
    memories = {"m1": m1, "m2": m2}
    results = compete(activations, memories, now=now)

    assert len(results) == 2
    assert results[0].memory.id == "m1"
    assert results[0].score > results[1].score


def test_status_penalty():
    """Superseded and contradicted memories should be penalized."""
    now = time.time()
    active = Memory(id="active", text="active", status="active",
                    strength=1.0, confidence=1.0, created_at=now, last_accessed=now)
    superseded = Memory(id="sup", text="superseded", status="superseded",
                        strength=1.0, confidence=1.0, created_at=now, last_accessed=now)

    activations = {"active": 1.0, "sup": 1.0}
    memories = {"active": active, "sup": superseded}
    results = compete(activations, memories, now=now)

    active_score = next(r for r in results if r.memory.id == "active").score
    sup_score = next(r for r in results if r.memory.id == "sup").score
    assert active_score > sup_score


def test_compete_empty():
    assert compete({}, {}) == []


def test_scored_memory_components():
    """Verify component breakdown is populated."""
    now = time.time()
    m = Memory(id="x", text="test", created_at=now, last_accessed=now)
    results = compete({"x": 1.0}, {"x": m}, now=now)
    assert len(results) == 1
    c = results[0].components
    assert "activation" in c
    assert "recency" in c
    assert "strength" in c
    assert "confidence" in c
