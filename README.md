# StudyMummy

StudyMummy ist eine agentische Lernplattform. Sie verarbeitet eigene Lernmaterialien, führt Lernende adaptiv durch Aufgaben und hält Lernfortschritt, Fehlerbilder und Dokumentwissen über mehrere Sitzungen verfügbar.

Der Chat ist als beobachtbarer Multi-Agent-Workflow umgesetzt: Ein Planning Agent wählt den nächsten Lernschritt, ein Tutor Agent führt ihn mit begrenzten Werkzeugrechten aus und ein Reviewer Agent kontrolliert die Antwort vor der Ausgabe. Alle Schritte werden typisiert und mit einer gemeinsamen Trace-ID protokolliert.

## Kernfunktionen

- Dokumentimport mit Text- und PDF-Verarbeitung
- Aufgaben-, Quiz- und Cheatsheet-Generierung
- adaptiver sokratischer Tutor mit vier Hilfestufen
- RAG über PostgreSQL und pgvector
- persistente Sitzungen, Dialoge und Lernprofile
- strukturierte Planung und kontrolliertes Tool-Calling
- Qualitätsprüfung jeder Tutorantwort
- Profile, Kalender, Social-Funktionen und Gamification

## Architektur

```mermaid
flowchart LR
    UI["Angular Frontend"] --> API["FastAPI"]
    API --> P["Perception"]
    P --> PL["Planning Agent"]
    PL --> T["Tutor Agent"]
    T --> TOOLS["Capability-scoped Tools"]
    TOOLS --> R["Reviewer Agent"]
    T --> R
    R --> M["Memory Update"]
    M --> DB[("PostgreSQL + pgvector")]
    R --> API
```

Eine detaillierte technische Beschreibung steht in [docs/architecture.md](docs/architecture.md). Die agentischen Eigenschaften und Abgrenzungen werden in [docs/agent-system.md](docs/agent-system.md) erläutert.

## Agenten-Workflow

Ein Chat-Turn durchläuft fünf explizite Phasen:

1. **Perceive:** Eingabe normalisieren, aktive Aufgabe und Dokumentkontext laden.
2. **Plan:** Absicht, nächste Aktion, Ziel, Erfolgskriterien und benötigte Tools bestimmen.
3. **Act:** Tutorantwort erzeugen und ausschließlich freigegebene Tools aufrufen.
4. **Review:** Antwort auf Fachlichkeit, Hilfestufe, Planerfüllung und Tooltreue prüfen.
5. **Remember:** Antwort und ausgeführte Aktion im Sitzungsverlauf speichern.

Die API gibt neben der Tutorantwort auch die Entscheidung und den kompakten Agenten-Trace zurück. Damit bleibt nachvollziehbar, welche Rollen beteiligt waren und welche Aktion ausgeführt wurde, ohne interne Gedankengänge offenzulegen.

## Technologie

| Bereich | Technologie |
|---|---|
| Frontend | Angular 22, TypeScript, PrimeNG, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy |
| LLM | OpenAI-kompatible Chat-Completions mit JSON-Modus und Function Calling |
| Daten | PostgreSQL 15, pgvector |
| Betrieb | Docker Compose |
| Tests | pytest, pytest-asyncio, Vitest |

## Schnellstart mit Docker

1. `.env.example` nach `.env` kopieren und die Modellkonfiguration anpassen.
2. Anwendung starten:

```bash
docker compose up --build
```

Danach sind erreichbar:

- Frontend: `http://localhost:4200`
- API: `http://localhost:8000`
- OpenAPI-Dokumentation: `http://localhost:8000/docs`

Die PostgreSQL-Verbindung wird durch Docker Compose eingerichtet. Lokal verwendet das Beispiel Port `5433`, innerhalb des Compose-Netzes Port `5432`.

## Lokale Entwicklung

Backend:

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload
uv run pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm start
npm test
```

## Verzeichnisstruktur

```text
backend/
  app/
    agents/          spezialisierte Agenten und Orchestrator
    api/             REST- und WebSocket-Endpunkte
    db/              SQLAlchemy-Modelle und Datenbankzugriff
    evaluation/      reproduzierbare Qualitätsmetriken
    models/          API- und Domänenmodelle
    services/        LLM, RAG, Dokumente und Sessions
    tools/           registrierte Agentenwerkzeuge
  tests/
frontend/
  src/app/
    core/            Authentifizierung, Layout und API-Services
    features/        fachliche UI-Bereiche
    shared/          wiederverwendbare Komponenten
docs/
  architecture.md
  agent-system.md
```

## Konfiguration

Die wichtigsten Umgebungsvariablen sind in `.env.example` dokumentiert:

- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`
- `OPENAI_TEMPERATURE`, `OPENAI_TIMEOUT_SECONDS`
- `DATABASE_URL`
- `EMBEDDING_MODEL`
- `AGENT_REVIEW_ENABLED`
- `SECRET_KEY`

Für produktive Umgebungen müssen ein eigener `SECRET_KEY`, eingeschränkte CORS-Origins und sichere Datenbankzugänge gesetzt werden.

## Qualitätsprinzipien

- Agentenentscheidungen sind strukturierte Daten statt freier Prompt-Interpretation.
- Tool-Rechte werden nach der Planung durch eine feste Policy reduziert.
- Dokumentinhalte gelten als nicht vertrauenswürdige Daten.
- Side Effects laufen ausschließlich über registrierte Tools.
- Bei nicht verfügbarem JSON-Modus greifen deterministische Planungs-Fallbacks.
- Tests benötigen keinen Live-API-Key.
