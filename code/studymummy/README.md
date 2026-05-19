# StudyMummy – FastAPI Backend

**WP Agentic AI, HAW Hamburg, SS 2026 | Übungsblatt 03**  
Erste Implementierung: LLM-Anbindung, Tool Use & RAG-Grundgerüst

---

## Architektur

```
app/
├── main.py                     # FastAPI App Factory + Lifespan
├── core/
│   ├── config.py               # Pydantic Settings (env-basiert)
│   └── logging.py              # Strukturiertes Logging mit trace_id
├── api/v1/
│   ├── router.py               # Zentraler API-Router
│   └── endpoints/
│       ├── agent.py            # Chat, Upload, Quiz, Cheatsheet
│       ├── memory.py           # Session & Lernprofil
│       └── tasks.py            # Task-CRUD
├── services/
│   ├── llm_service.py          # OpenAI-Anbindung + ReAct-Tool-Loop
│   ├── rag_service.py          # RAG-Retrieval (Mock → ChromaDB)
│   └── session_service.py      # Working Memory + Lernprofile
├── tools/
│   ├── registry.py             # Zentrales Tool-Registry
│   └── study_tools.py          # evaluate_answer, update_learning_profile, ...
├── middleware/
│   └── logging_middleware.py   # Request-Tracing
└── models/
    ├── task.py                  # Task, TaskStatus
    ├── memory.py                # WorkingMemory, LearningProfile
    └── agent.py                 # Request/Response-Schemas
```

### Kognitive Schichten → Code-Mapping

| Schicht (Übungsblatt 02) | Implementierung |
|---|---|
| **Perception** | `POST /agent/upload` → `llm_service.extract_tasks_from_text()` |
| **Memory** | `session_service.py` (Working) + RAG (Semantic) + Lernprofil (Episodic) |
| **Planning** | ReAct-Loop in `llm_service.chat_with_tools()` |
| **Action** | Tool-Registry + Tools in `study_tools.py` |

---

## Quickstart

```bash
# 1. Dependencies installieren
pip install -e ".[rag]"

# 2. API-Key setzen
cp .env.example .env
# OPENAI_API_KEY=sk-... in .env eintragen

# 3. Server starten
uvicorn app.main:app --reload

# 4. Docs öffnen
open http://localhost:8000/docs
```

## Tests ausführen

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Neues Tool hinzufügen

```python
# app/tools/study_tools.py
async def _my_new_tool(param: str) -> dict:
    return {"result": param}

register(ToolDefinition(
    name="my_new_tool",
    description="Beschreibung für das LLM",
    parameters={"type": "object", "properties": {"param": {"type": "string"}}, "required": ["param"]},
    fn=_my_new_tool,
))
```

Das Tool ist sofort über Function Calling verfügbar – keine weitere Änderung nötig.

---

## Nächste Schritte (Übungsblatt 04+)

- [ ] ChromaDB-Anbindung für echtes Embedding-Retrieval (`rag_service.py`)
- [ ] PostgreSQL/Supabase für persistente Sessions und Lernprofile
- [ ] PyMuPDF für PDF-Textextraktion im Upload-Endpunkt
- [ ] Multi-Agent: Orchestrator + spezialisierte Worker (Tutor, Quiz-Generator, Cheatsheet-Agent)
- [ ] Guardrails gegen Prompt Injection (Übungsblatt 06)
