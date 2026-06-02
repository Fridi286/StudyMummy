# Deliverable-Checkliste – WP Agentic AI

**Modul:** WP Agentic AI · HAW Hamburg · SS 2026
**Zweck:** Vollständigkeitskontrolle aller Pflicht-Deliverables über die sechs Praktikumstermine plus Abschlusspräsentation.
**Verwendung:** Jede Gruppe hakt am Ende eines Termins die erledigten Punkte ab. Der Dozent nutzt dieselbe Liste zur Abnahme.

---

## Vorab auszufüllen

- **Gruppe / Teamname:** ______________________________
- **Gruppenmitglieder:** ______________________________
- **Gewähltes Projekt (1–6 bzw. eigener Vorschlag):** ______________________________
- **Repository-Link (GitHub):** ______________________________

> Hinweis: Eigene Projektvorschläge müssen mindestens die Eigenschaften Perception, Planning und Action umfassen und vorab mit dem Dozenten abgestimmt sein. Abgaben erfolgen über Moodle; Prof. Clemen (`tomclemen`) muss als Mitglied im GitHub-Repository eingeladen sein.

---

## Übergreifende Aufgaben (gesamtes Semester)

- [ ] GitHub-Repository angelegt (nicht GitLab)
- [ ] Prof. Clemen (`tomclemen`) als Mitglied eingeladen
- [ ] `README.md` enthält: Projektname, alle Teammitglieder + Rollen, gewähltes Projekt, einen Absatz „Was wollen wir bauen?"
- [ ] Repository wird tagesaktuell gepflegt (Code + Dokumentation als Markdown)

---

## Termin 1 – Projektdefinition & Agentenanalyse
*Begleitend zu Kapitel 01: Agents (Fundamentals)*

**Ziel:** Gruppe steht, Projekt gewählt, Repository existiert, erste Systemanalyse abgeschlossen.

- [ ] Gruppe gebildet (max. 5 Personen)
- [ ] Projekt gewählt **und beim Dozenten gemeldet**
- [ ] Elevator Pitch formuliert (2–3 Sätze: Was soll der Agent können?)
- [ ] Rollen in der Gruppe verteilt (Repo/CI, Doku, Dozentenkontakt)
- [ ] Tooling-Frage geklärt (LLM-Zugriff, Frameworks, API-Keys) und Basis-Pakete installiert

**PEAS-Analyse**
- [ ] PEAS-Tabelle vollständig ausgefüllt:
  - [ ] Performance Measure (Woran erkennt man Erfolg?)
  - [ ] Environment (In welcher Umgebung agiert der Agent?)
  - [ ] Actuators (Welche Aktionen kann er ausführen?)
  - [ ] Sensors (Welche Eingaben erhält er?)
- [ ] Umgebungseigenschaften auf allen 7 Dimensionen eingeordnet (mit Begründung): fully/partially observable · deterministic/stochastic · episodic/sequential · static/dynamic · discrete/continuous · single/multi-agent · known/unknown
- [ ] Agententyp bestimmt (Simple Reflex → Learning Agent) + Begründung

**Pflicht-Deliverable Termin 1**

- [ ] `README.md` im Repo mit: Projektname, Gruppe, Projektbeschreibung, erster Architekturskizze (Foto oder Diagramm: Agenten/Komponenten, Kommunikation, benötigte externe Tools/APIs)
- [ ] Projektdokument (1–2 Seiten) im Repo: Elevator Pitch + PEAS-Tabelle + Umgebungseinordnung + Agententyp
- [ ] „Hello, LLM"-Skript läuft **bei allen Gruppenmitgliedern lokal**

---

## Termin 2 – Architekturentwurf: Kognitive Schichten
*Begleitend zu Kapitel 02: Perception, Memory & Planning*

**Ziel:** Aus der Skizze wird ein bewusst entworfenes Design; ein minimaler End-to-End-Prototyp läuft.

- [ ] 4-Schichten-Architektur für das eigene Projekt **schriftlich** ausgearbeitet:
  - [ ] **Perception** – Inputs definiert, Vorverarbeitung beschrieben
  - [ ] **Memory** – benötigte Memory-Typen identifiziert (Working / Episodic / Semantic); wo reicht das Context Window, wo braucht ihr mehr?
  - [ ] **Planning** – reaktiv vs. deliberativ entschieden, Planungslogik beschrieben
  - [ ] **Action** – Aktionen definiert, Seiteneffekte identifiziert
- [ ] Agenten-/Komponenten-Zuordnung zur Russell/Norvig-Taxonomie dokumentiert
- [ ] Minimaler End-to-End-Durchlauf implementiert (Funktion vor Eleganz)
- [ ] Erste Stolpersteine festgehalten (unklare Doku, Improvisationen, getroffene Annahmen)
- [ ] Technische Bausteine pro Schicht recherchiert (LLM, Datenquellen, APIs); offene Fragen für Termin 3 notiert

**Pflicht-Deliverable Termin 2**

- [ ] Architekturdokument (1–2 Seiten) mit 4-Schichten-Mapping + Architekturdiagramm (Schichten + Datenfluss) + kritische Schichten markiert + mindestens eine Schwäche benannt
- [ ] Lauffähiger Prototyp im Repo **mit Anleitung zum Starten**
- [ ] Kurze Liste offener Fragen für Termin 3

---

## Termin 3 – Erste Implementierung: LLM, RAG & Tool Use
*Begleitend zu Kapitel 03: LLMs, RAG & Tool Use*

**Ziel:** Das System tut, was es tun soll – zumindest im Standardfall.

- [ ] Entwicklungsumgebung vollständig eingerichtet (Python, API-Keys, Dependencies)
- [ ] LLM-Call für den Use Case implementiert (mit System Prompt); Grenzen des Basis-LLM dokumentiert
- [ ] Entscheidung getroffen (RAG oder Tool Use) + Begründung dokumentiert:
  - [ ] **Option RAG:** Wissensbasis vorbereitet → Retrieval-Pipeline implementiert (z. B. Vector Store) → Verbesserung gegenüber Baseline dokumentiert
  - [ ] **Option Tool Use:** 2–3 Tools/Functions definiert → Mock-Implementierungen erstellt → Function Calling ans LLM angebunden
- [ ] Mehrere End-to-End-Durchläufe durchgeführt und protokolliert (Varianz beobachtet)
- [ ] Auffälliges/unerwartetes Systemverhalten notiert

**Pflicht-Deliverable Termin 3**

- [ ] Lauffähige Kernfunktionalität im Repo (LLM + RAG oder Tool Use)
- [ ] Kurzes **Lab Notebook** (Markdown-Datei im Repo) mit: was funktioniert / was bricht / Beobachtungen aus den Durchläufen

---

## Termin 4 – Erweiterung: Multi-Agent oder Vertiefung + Robustheit
*Begleitend zu Kapitel 04: Multi-Agent Systems*

**Ziel:** Das System überlebt ungewöhnliche Eingaben; Architektur ist bewusst skaliert oder vertieft; das Innenleben ist nachvollziehbar.

**Architekturentscheidung**
- [ ] Heuristik geprüft: unabhängige Teilaufgaben? Würde Parallelisierung den Durchsatz erhöhen?
- [ ] Entscheidung begründet dokumentiert:
  - [ ] **Pfad A – Multi-Agent:** Rollen definiert (System Prompt + Toolset + Scope) → Kommunikation implementiert (Shared State oder Message Passing) → Durchlauf mit ≥ 2 zusammenarbeitenden Workern erfolgreich
  - [ ] **Pfad B – Vertiefung:** zweite Lücke (RAG oder Tool Use) geschlossen → ReAct-Pattern implementiert (Thought → Action → Observation) → mindestens ein neues Feature hinzugefügt

**Robustheit & Observability**
- [ ] **Observability** eingebaut: strukturiertes Logging aller LLM-Aufrufe (Prompt, Response, Latenz)
- [ ] Mindestens **3 Failure Modes / Edge Cases** identifiziert (z. B. leere/absurde Eingabe, API-Ausfall, falsches Output-Format)
- [ ] Sinnvolle Fehlerbehandlung implementiert (Retry / Fallback / Graceful Degradation) für mindestens 2 davon
- [ ] Zwischenpräsentation gehalten (max. 3 Minuten), Feedback erhalten und schriftlich notiert; Prioritäten für Termin 5 und 6 festgelegt

**Pflicht-Deliverable Termin 4**

- [ ] Begründete Architekturentscheidung (Multi-Agent vs. Vertiefung) im Repo
- [ ] Observability-Setup aktiv und produziert Logs
- [ ] Dokumentierte Edge-Case-Liste mit je: erwartetes Verhalten / tatsächliches Verhalten / gewählter Lösungsansatz
- [ ] Feedback-Notizen aus der Zwischenpräsentation

---

## Termin 5 – Evaluation & Experiment
*Begleitend zu Kapitel 05: Agentic AI Engineering*

**Ziel:** Belegen, *wie gut* das System ist – und unter welchen Bedingungen es versagt.

- [ ] Mindestens **eine quantitative und eine qualitative Metrik** definiert
- [ ] **Eine konkrete Hypothese** formuliert, die experimentell überprüft wird
- [ ] Mindestens **3 semantische Tests** geschrieben (keine exakten Stringvergleiche: Enthält die Antwort ein Datum? Ruft der Agent die richtigen Tools auf?)
- [ ] Experiment durchgeführt mit **mindestens 3 Durchläufen pro Variante**; alle Ergebnisse dokumentiert (auch unerwartete)
- [ ] Iteration: bei aufgedeckten Schwächen eine Komponente verbessert und erneut gemessen
- [ ] 2 Durchläufe mit gleicher Eingabe verglichen (Traces); Unterschiede bewertet
- [ ] Architekturdiagramm aktualisiert (Fehlerbehandlung + Tracing-Punkte eingezeichnet)

**Pflicht-Deliverable Termin 5**

- [ ] Metriken-Definition im Repo
- [ ] Hypothesen-Dokument mit Versuchsaufbau und Ergebnissen (Tabellen, ggf. Plots)
- [ ] Schriftliche Reflexion: Was wurde gelernt – über das System und über Agentic AI im Allgemeinen?

---

## Termin 6 – Safety, Guardrails & Generalprobe
*Begleitend zu Kapitel 06: Safety + Guardrails*

**Ziel:** Guardrails implementiert, Repo aufgeräumt, Präsentation und Demo sind bereit.

**Safety & Guardrails**
- [ ] Risikoanalyse durchgeführt (Prompt Injection, Goal Misgeneralization, Unintended Side Effects)
- [ ] Mindestens **2 Guardrail-Mechanismen** implementiert, z. B.: Input-Filterung · Output-Monitoring · Scope-Einschränkungen · Human-in-the-Loop
- [ ] Konkreten Guardrail-Fall demonstriert (z. B. bösartige Eingabe wird abgefangen)

**Präsentationsvorbereitung**
- [ ] Repository aufgeräumt: Code formatiert, ungenutzte Dateien entfernt, README aktualisiert, Abhängigkeiten dokumentiert (`requirements.txt` / `pyproject.toml`)
- [ ] **Projekt-Dokumentation (4–8 Seiten)** geschrieben, enthält:
  - [ ] Motivation und Zielsetzung
  - [ ] Architekturüberblick (mit Diagramm)
  - [ ] Designentscheidungen und ihre Begründung
  - [ ] Evaluation und Ergebnisse
  - [ ] Limitationen und Failure Modes
  - [ ] Was man mit mehr Zeit anders/zusätzlich machen würde
- [ ] **Präsentationsfolien (10–15 Folien)** erstellt – Struktur: Problem & Motivation / Lösungsansatz & Architektur / Demo / Evaluation & Ergebnisse / Safety & Guardrails / Erkenntnisse & Limitationen / Fazit
- [ ] **Live-Demo** vorbereitet (Use Case, benötigte Daten, Notfallplan bei Fehlschlag)
- [ ] **Backup-Video** der Demo erstellt (kurzer Bildschirmmitschnitt)
- [ ] **Trockenlauf** in der Gruppe durchgeführt (Zeit gestoppt, alle reden mindestens einmal)

**Pflicht-Deliverable Termin 6**

- [ ] Aufgeräumtes Repo mit vollständiger Projekt-Dokumentation
- [ ] Präsentationsfolien im Repo
- [ ] Backup-Demo-Video im Repo

---

## Termin 7 – Abschlusspräsentation (7. Juli 2026)
*Format: 15–20 Min. Vortrag inkl. Live-Demo, danach ca. 10 Min. Diskussion*

- [ ] Vortrag mit Live-Demo gehalten
- [ ] Diskussion bestritten (Fragen zu Designentscheidungen, Trade-offs, Failure Modes)
- [ ] Jedes Gruppenmitglied hat mindestens einen inhaltlichen Beitrag geleistet
- [ ] Andere Projekte anhand der PEAS-Kriterien bewertet (Ist das wirklich ein Agent? Welche Schichten sind stark/schwach besetzt?)
- [ ] **Übergabe:** finale Dokumentation **und** Repository-Link an den Dozenten

---

## Finale Artefakt-Übersicht (Schnellkontrolle)

Alle nachfolgenden Artefakte sollten am Ende im Repository vorhanden sein:

- [ ] `README.md` (Projektinfo, Gruppe, Architekturskizze – aktuell gehalten)
- [ ] Projektdokument: Elevator Pitch + PEAS-Analyse + Umgebungseinordnung + Agententyp (Termin 1)
- [ ] Architekturdokument mit 4-Schichten-Mapping + Diagramm (Termin 2)
- [ ] Lauffähiges System mit Start-Anleitung (Termin 3)
- [ ] Lab Notebook (Beobachtungen aus Durchläufen, Termin 3)
- [ ] Observability-Logs / Logging-Setup (Termin 4)
- [ ] Edge-Case-Liste mit Lösungsansätzen (Termin 4)
- [ ] Metriken-Definition (Termin 5)
- [ ] Hypothesen-Dokument mit Versuchsaufbau + Ergebnissen (Termin 5)
- [ ] Schriftliche Reflexion (Termin 5)
- [ ] Guardrail-Implementierung und -Demonstration (Termin 6)
- [ ] Projekt-Dokumentation (4–8 Seiten, Termin 6)
- [ ] Präsentationsfolien (Termin 6)
- [ ] Backup-Demo-Video (Termin 6)
- [ ] Transparenz-Hinweis zur Nutzung von KI-/Coding-Assistenten (wer/was beigetragen hat)
