"""OpenMem Web UI — lightweight local web interface for browsing memories."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request

from openmem import MemoryEngine

DEFAULT_DB = os.path.join(Path.home(), ".openmem", "memories.db")


def _get_db_path() -> str:
    return os.environ.get("OPENMEM_DB", DEFAULT_DB)


def _memory_to_dict(mem) -> dict:
    return {
        "id": mem.id,
        "type": mem.type,
        "text": mem.text,
        "gist": mem.gist,
        "entities": mem.entities,
        "created_at": mem.created_at,
        "updated_at": mem.updated_at,
        "strength": mem.strength,
        "confidence": mem.confidence,
        "access_count": mem.access_count,
        "last_accessed": mem.last_accessed,
        "status": mem.status,
    }


def _edge_to_dict(edge) -> dict:
    return {
        "id": edge.id,
        "source_id": edge.source_id,
        "target_id": edge.target_id,
        "rel_type": edge.rel_type,
        "weight": edge.weight,
        "created_at": edge.created_at,
    }


def create_app(db_path: str | None = None) -> Flask:
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="/static")

    db = db_path or _get_db_path()

    def get_engine() -> MemoryEngine:
        return MemoryEngine(db_path=db)

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/api/stats")
    def api_stats():
        engine = get_engine()
        return jsonify(engine.stats())

    @app.route("/api/memories")
    def api_memories():
        engine = get_engine()
        memories = engine.store.all_memories()

        # Filter by type
        mem_type = request.args.get("type")
        if mem_type:
            memories = [m for m in memories if m.type == mem_type]

        # Filter by status
        mem_status = request.args.get("status")
        if mem_status:
            memories = [m for m in memories if m.status == mem_status]

        # Sort
        sort_by = request.args.get("sort", "created_at")
        reverse = request.args.get("order", "desc") == "desc"
        if sort_by in ("created_at", "updated_at", "strength", "confidence", "access_count"):
            memories.sort(key=lambda m: getattr(m, sort_by) or 0, reverse=reverse)
        elif sort_by == "type":
            memories.sort(key=lambda m: m.type, reverse=reverse)
        elif sort_by == "status":
            memories.sort(key=lambda m: m.status, reverse=reverse)

        return jsonify([_memory_to_dict(m) for m in memories])

    @app.route("/api/memories/<memory_id>")
    def api_memory_detail(memory_id):
        engine = get_engine()

        mem = engine.store.get_memory(memory_id)
        # Try prefix match
        if not mem:
            for m in engine.store.all_memories():
                if m.id.startswith(memory_id):
                    mem = m
                    break

        if not mem:
            return jsonify({"error": "Memory not found"}), 404

        edges = engine.store.get_edges(mem.id)
        seen = set()
        unique_edges = []
        for e in edges:
            if e.id not in seen:
                seen.add(e.id)
                unique_edges.append(_edge_to_dict(e))

        result = _memory_to_dict(mem)
        result["edges"] = unique_edges
        return jsonify(result)

    @app.route("/api/search")
    def api_search():
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify([])

        engine = get_engine()
        top_k = request.args.get("top_k", 10, type=int)
        results = engine.recall(query, top_k=top_k, token_budget=8000)

        return jsonify([
            {
                **_memory_to_dict(sm.memory),
                "score": round(sm.score, 4),
                "activation": round(sm.activation, 4),
            }
            for sm in results
        ])

    @app.route("/api/memories/<memory_id>/reinforce", methods=["POST"])
    def api_reinforce(memory_id):
        engine = get_engine()
        mem = engine.store.get_memory(memory_id)
        if not mem:
            return jsonify({"error": "Memory not found"}), 404

        engine.reinforce(memory_id)
        updated = engine.store.get_memory(memory_id)
        return jsonify(_memory_to_dict(updated))

    @app.route("/api/memories/<memory_id>", methods=["DELETE"])
    def api_delete_memory(memory_id):
        engine = get_engine()
        mem = engine.store.get_memory(memory_id)
        if not mem:
            return jsonify({"error": "Memory not found"}), 404

        mem.status = "deleted"
        engine.store.update_memory(mem)
        return jsonify({"ok": True})

    return app
