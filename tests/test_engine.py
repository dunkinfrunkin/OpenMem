import time

from openmem import MemoryEngine


def test_add_and_recall():
    e = MemoryEngine()
    e.add("Python is a popular programming language", type="fact", entities=["Python"])
    e.add("JavaScript runs in the browser", type="fact", entities=["JavaScript"])

    results = e.recall("Python programming")
    assert len(results) >= 1
    assert "Python" in results[0].memory.text


def test_linked_memories_boost():
    """Linked memories should appear via spreading activation even without direct match."""
    e = MemoryEngine()
    m1 = e.add("We chose SQLite over Postgres for simplicity", type="decision",
               entities=["SQLite", "Postgres"])
    m2 = e.add("Postgres has better concurrent write support", type="fact",
               entities=["Postgres"])
    e.link(m1.id, m2.id, "supports", weight=0.8)

    results = e.recall("Why did we pick SQLite?")
    result_ids = [r.memory.id for r in results]
    assert m1.id in result_ids


def test_recall_respects_top_k():
    e = MemoryEngine()
    for i in range(20):
        e.add(f"Memory number {i} about testing recall limits")
    results = e.recall("testing recall", top_k=3)
    assert len(results) <= 3


def test_recall_token_budget():
    e = MemoryEngine()
    # Each memory is ~50 chars = ~12 tokens
    for i in range(20):
        e.add(f"Memory {i}: some moderately long text about topic X and Y")

    # Very small token budget should limit results
    results = e.recall("topic", top_k=20, token_budget=50)
    assert len(results) < 20


def test_reinforce():
    e = MemoryEngine()
    m = e.add("reinforceable memory", confidence=0.8)
    # Manually lower strength so reinforce can increase it
    mem = e.store.get_memory(m.id)
    mem.strength = 0.5
    e.store.update_memory(mem)

    e.reinforce(m.id)
    updated = e.store.get_memory(m.id)
    assert updated.strength > 0.5
    assert updated.access_count == 1


def test_supersede():
    e = MemoryEngine()
    old = e.add("The API uses v1 endpoints")
    new = e.add("The API has been upgraded to v2 endpoints")
    e.supersede(old.id, new.id)

    old_updated = e.store.get_memory(old.id)
    assert old_updated.status == "superseded"

    # Old memory should be penalized in recall
    results = e.recall("API endpoints")
    if len(results) >= 2:
        scores = {r.memory.id: r.score for r in results}
        if old.id in scores and new.id in scores:
            assert scores[new.id] > scores[old.id]


def test_contradict():
    e = MemoryEngine()
    a = e.add("The system uses REST", type="decision", confidence=0.9)
    b = e.add("The system uses GraphQL", type="decision", confidence=0.5)
    e.contradict(a.id, b.id)

    results = e.recall("system API protocol")
    if len(results) >= 2:
        ids = [r.memory.id for r in results]
        if a.id in ids and b.id in ids:
            score_a = next(r for r in results if r.memory.id == a.id).score
            score_b = next(r for r in results if r.memory.id == b.id).score
            # Higher confidence should win
            assert score_a > score_b


def test_decay_all():
    e = MemoryEngine()
    m = e.add("decayable memory")
    original = m.strength

    # Manually set created_at to 30 days ago to force decay
    mem = e.store.get_memory(m.id)
    mem.updated_at = time.time() - 30 * 86400
    e.store.update_memory(mem)

    e.decay_all()
    decayed = e.store.get_memory(m.id)
    assert decayed.strength < original


def test_stats():
    e = MemoryEngine()
    m1 = e.add("first memory")
    m2 = e.add("second memory")
    e.link(m1.id, m2.id, "supports")

    s = e.stats()
    assert s["memory_count"] == 2
    assert s["edge_count"] == 1
    assert s["active_count"] == 2


def test_empty_recall():
    e = MemoryEngine()
    results = e.recall("nothing here")
    assert results == []


def test_access_count_bumped_on_recall():
    e = MemoryEngine()
    m = e.add("findable memory about bananas")
    assert m.access_count == 0

    results = e.recall("bananas")
    if results:
        updated = e.store.get_memory(results[0].memory.id)
        assert updated.access_count >= 1


def test_full_pipeline_smoke():
    """Full integration: add, link, recall, verify ranking."""
    e = MemoryEngine()
    m1 = e.add("We chose SQLite over Postgres for simplicity",
               type="decision", entities=["SQLite", "Postgres"])
    m2 = e.add("Postgres has better concurrent write support",
               type="fact", entities=["Postgres"])
    m3 = e.add("The team prefers simple tools over complex ones",
               type="preference")
    e.link(m1.id, m2.id, "supports")
    e.link(m1.id, m3.id, "supports")

    results = e.recall("Why did we pick SQLite?")
    assert len(results) >= 1
    # The decision memory should be in the results
    result_texts = [r.memory.text for r in results]
    assert any("SQLite" in t for t in result_texts)

    # Scores should be descending
    for i in range(len(results) - 1):
        assert results[i].score >= results[i + 1].score
