from __future__ import annotations

import json
import sqlite3
import time
from typing import Optional

from .models import Edge, Memory


class SQLiteStore:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL DEFAULT 'fact',
                text TEXT NOT NULL,
                gist TEXT,
                entities TEXT NOT NULL DEFAULT '[]',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                strength REAL NOT NULL DEFAULT 1.0,
                confidence REAL NOT NULL DEFAULT 1.0,
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed REAL,
                status TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                rel_type TEXT NOT NULL DEFAULT 'mentions',
                weight REAL NOT NULL DEFAULT 0.5,
                created_at REAL NOT NULL,
                FOREIGN KEY (source_id) REFERENCES memories(id),
                FOREIGN KEY (target_id) REFERENCES memories(id)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                text,
                gist,
                entities,
                content='memories',
                content_rowid='rowid'
            );

            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, id, text, gist, entities)
                VALUES (new.rowid, new.id, new.text, new.gist, new.entities);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, id, text, gist, entities)
                VALUES ('delete', old.rowid, old.id, old.text, old.gist, old.entities);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, id, text, gist, entities)
                VALUES ('delete', old.rowid, old.id, old.text, old.gist, old.entities);
                INSERT INTO memories_fts(rowid, id, text, gist, entities)
                VALUES (new.rowid, new.id, new.text, new.gist, new.entities);
            END;
        """)
        self.conn.commit()

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        return Memory(
            id=row["id"],
            type=row["type"],
            text=row["text"],
            gist=row["gist"],
            entities=json.loads(row["entities"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            strength=row["strength"],
            confidence=row["confidence"],
            access_count=row["access_count"],
            last_accessed=row["last_accessed"],
            status=row["status"],
        )

    def _row_to_edge(self, row: sqlite3.Row) -> Edge:
        return Edge(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            rel_type=row["rel_type"],
            weight=row["weight"],
            created_at=row["created_at"],
        )

    def add_memory(self, memory: Memory) -> Memory:
        entities_json = json.dumps(memory.entities)
        self.conn.execute(
            """INSERT INTO memories (id, type, text, gist, entities, created_at,
               updated_at, strength, confidence, access_count, last_accessed, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory.id, memory.type, memory.text, memory.gist, entities_json,
                memory.created_at, memory.updated_at, memory.strength,
                memory.confidence, memory.access_count, memory.last_accessed,
                memory.status,
            ),
        )
        self.conn.commit()
        return memory

    def add_edge(self, edge: Edge) -> Edge:
        self.conn.execute(
            """INSERT INTO edges (id, source_id, target_id, rel_type, weight, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (edge.id, edge.source_id, edge.target_id, edge.rel_type,
             edge.weight, edge.created_at),
        )
        self.conn.commit()
        return edge

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        row = self.conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        return self._row_to_memory(row) if row else None

    def get_edges(self, memory_id: str) -> list[Edge]:
        rows = self.conn.execute(
            "SELECT * FROM edges WHERE source_id = ? OR target_id = ?",
            (memory_id, memory_id),
        ).fetchall()
        return [self._row_to_edge(r) for r in rows]

    def get_neighbors(self, memory_id: str) -> list[tuple[Edge, Memory]]:
        edges = self.get_edges(memory_id)
        result = []
        for edge in edges:
            neighbor_id = edge.target_id if edge.source_id == memory_id else edge.source_id
            neighbor = self.get_memory(neighbor_id)
            if neighbor:
                result.append((edge, neighbor))
        return result

    def search_bm25(self, query: str, limit: int = 20) -> list[tuple[str, float]]:
        """FTS5 MATCH with BM25 ranking. Returns (memory_id, bm25_score) pairs."""
        # Escape special FTS5 characters in the query
        safe_query = self._escape_fts_query(query)
        if not safe_query.strip():
            return []
        rows = self.conn.execute(
            """SELECT id, bm25(memories_fts) as rank
               FROM memories_fts
               WHERE memories_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (safe_query, limit),
        ).fetchall()
        # bm25() returns negative scores (lower = better match), negate for positive scores
        return [(row["id"], -row["rank"]) for row in rows]

    def _escape_fts_query(self, query: str) -> str:
        """Turn a raw user query into a safe FTS5 query by quoting each token."""
        tokens = query.split()
        if not tokens:
            return ""
        # Quote each token to avoid FTS5 syntax errors from special chars
        quoted = ['"' + t.replace('"', '""') + '"' for t in tokens]
        return " OR ".join(quoted)

    def update_access(self, memory_id: str) -> None:
        now = time.time()
        self.conn.execute(
            """UPDATE memories SET access_count = access_count + 1,
               last_accessed = ?, updated_at = ? WHERE id = ?""",
            (now, now, memory_id),
        )
        self.conn.commit()

    def update_memory(self, memory: Memory) -> None:
        entities_json = json.dumps(memory.entities)
        self.conn.execute(
            """UPDATE memories SET type=?, text=?, gist=?, entities=?,
               updated_at=?, strength=?, confidence=?, access_count=?,
               last_accessed=?, status=? WHERE id=?""",
            (
                memory.type, memory.text, memory.gist, entities_json,
                memory.updated_at, memory.strength, memory.confidence,
                memory.access_count, memory.last_accessed, memory.status,
                memory.id,
            ),
        )
        self.conn.commit()

    def all_memories(self) -> list[Memory]:
        rows = self.conn.execute("SELECT * FROM memories").fetchall()
        return [self._row_to_memory(r) for r in rows]

    def close(self) -> None:
        self.conn.close()
