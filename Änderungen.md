# Änderungen seit dem übernommenen StudyMummy-Ausgangsstand
## 1. Agentischer Tutor und Multi-Agent-System

- Der ursprüngliche direkte Tutor-Aufruf im Endpunkt `/agent/chat` wurde durch
  ein hierarchisches, nachrichtengetriebenes Multi-Agent-System ersetzt.
- Planning Agent, Tutor Agent und Reviewer Agent besitzen getrennte Ziele,
  Capabilities und lokale Laufzeitzustände. Sie implementieren einen gemeinsamen
  `MASAgent`-Vertrag.
- Ein run-lokaler `MASMessageBus` übermittelt typisierte Nachrichten. Ein
  `AgentBlackboard` hält Plan, Entwurf, Review und Werkzeugbeobachtungen des
  aktuellen Turns.
- Der normale Ablauf lautet Planning, Ausführung und Review. Der Reviewer kann
  eine textuelle Revision beim Tutor oder eine Neuplanung beim Planner auslösen.
  Die Zahl der Koordinationsrunden ist auf eins bis vier begrenzt und beträgt
  standardmäßig zwei.
- Der Orchestrator verteilt Nachrichten, setzt Laufzeitgrenzen und erstellt den
  Trace. Fachliche Folgeentscheidungen werden von den Agenten getroffen.
- Die API-Antwort enthält neben dem Tutor-Text den Plan, beteiligte Agenten,
  Kommunikationsschritte, Toolbeobachtungen und einen kompakten Agenten-Trace.
  Das Frontend zeigt daraus eine aufklappbare Zusammenfassung, ohne interne
  Gedankengänge offenzulegen.

## 2. Kontext, Gedächtnis und RAG

- Der Chat baut pro Turn einen typisierten `AgentContext` aus authentifiziertem
  Nutzer, Sitzung, Hilfestufe, Aufgabe, Dialoghistorie, Frontend-Kontext und
  abgerufenem Dokumentwissen auf.
- Aufgaben- und Dokumentkontext werden auf Eigentum des angemeldeten Nutzers
  geprüft. Im Learn-Tab wird die ID des geöffneten Dokuments an den Tutor
  übergeben; das Retrieval kann dadurch auf dieses Dokument eingeschränkt werden.
- Sitzungen und Chatlogs bleiben persistent. Plan, Review, lokale
  Agentenzustände und typisierte Toolbeobachtungen sind dagegen bewusst
  turn-lokal.
- Dokument-, Aufgaben- und Frontend-Kontext werden im Tutor- und
  Reviewer-Prompt als nicht vertrauenswürdige Lerndaten markiert. Direkte
  Nutzereingaben werden zusätzlich normalisiert und gegen einfache
  Prompt-Injection-Muster geprüft.
- RAG-Fehler lassen den Chat weiterhin ohne Dokumentkontext fortfahren, statt
  den gesamten Request abzubrechen. Dieser Fallback erhöht die Verfügbarkeit,
  unterscheidet in der Antwort aber nicht sicher zwischen keinem Treffer und
  einem Retrievalfehler.

## 3. Tool Use und persistente Aktionen

- Die Tool-Registry wurde in den MAS-Ablauf eingebunden. Eine
  `SAFE_TOOL_POLICY` reduziert die vom Planner vorgeschlagenen Werkzeuge noch
  einmal abhängig von der geplanten Aktion.
- Im Chat sind Antwortbewertung, Lernprofil-Update, Coins/Erfahrung und
  Kalendernotizen erreichbar. Unbekannte oder nicht freigegebene Toolnamen
  werden blockiert.
- Toolaufrufe werden als typisierte Beobachtungen mit den Zuständen `succeeded`,
  `failed`, `blocked` oder `invalid_arguments` protokolliert. Die verkürzte
  `tool_calls`-Liste enthält nur erfolgreich beendete Funktionen.
- Nutzeridentitäten für Lernprofil, Belohnung und Kalender stammen aus dem
  authentifizierten Request-Kontext und nicht aus frei erzeugten
  Modellargumenten.
- Belohnungen prüfen Aufgabeneigentum, begrenzen Beträge und verhindern unter
  Sperre eine doppelte Vergabe. Kalendertermine werden auf ISO-Zeitstempel,
  kompatible Zeitzonen und ein positives Zeitintervall geprüft.
- `generate_quiz_questions` und `create_cheatsheet` bleiben registrierte
  Mock-Tools, sind jedoch nicht für den Tutor-Chat freigegeben. Quiz und
  Merkblatt im Learn-Tab entstehen stattdessen durch die Hintergrundanalyse
  hochgeladener Dokumente.

## 4. Learn-Tab und Dokumentverarbeitung

- Nach Auswahl eines Dokuments werden Aufgaben, Quiz und Merkblatt gemeinsam
  geladen. Ladezustand, API-Fehler und ein Dokument ohne erzeugte Lernartefakte
  werden in der Oberfläche getrennt dargestellt.
- Für lesbare Dokumente ohne erzeugte Artefakte wurde ein kontrollierter
  Reanalyse-Endpunkt ergänzt. Eine Reanalyse ist nur erlaubt, wenn noch keine
  Aufgaben, Quizdaten, Merkblätter oder Vektorchunks existieren, damit keine
  Duplikate entstehen.
- Der Dokument-Analyzer meldet einen Fehler, wenn zwar Text gelesen, aber kein
  einziges Lernartefakt erzeugt wurde. Zuvor konnte dieser Fall wie eine
  erfolgreiche Analyse wirken.
- Die Upload-Grenze wurde von 5 MB auf 20 MB erhöht.
- Die Study Library schließt auf kleinen Bildschirmen nach einer Auswahl und
  verwendet ein sichtbares Schließsymbol. Dokument- und Chat-Aktionsmenüs nutzen
  die neue gemeinsame `ActionMenuComponent`, wodurch die zuvor teilweise nicht
  sichtbaren Popup-Menüs ersetzt wurden.
- Der aktuell gewählte Aufgaben- und Dokumentkontext wird an den AI-Tutor
  weitergegeben. Dadurch beziehen sich Hilfen gezielter auf die aktive
  Lernansicht.

## 5. OpenAI-Kompatibilität und Konfiguration

- Die LLM-Anbindung wurde für OpenAI-kompatible Endpunkte vereinheitlicht.
  Strukturierte Planner- und Reviewer-Antworten sowie Function Calling des
  Tutors werden zentral über den Modelladapter verarbeitet.
- Modellspezifische Parameter werden kompatibel gesetzt: Reasoning-Modelle
  erhalten keinen Temperaturwert; beim GPT-5-Function-Calling wird
  `reasoning_effort=none` verwendet
- Die Compose-Konfiguration setzt sinnvolle Defaults für Modell,
  Embedding-Modell und HAW-Endpunkt, ohne einen vorhandenen OpenAI-Schlüssel im
  Repository zu hinterlegen.
- Die Produktionskonfiguration verwirft beim Anwendungsstart bekannte
  `SECRET_KEY`-Platzhalter und Schlüssel unter 32 Zeichen. Die Datenbank wird am
  Host nur an Loopback gebunden; Backend und Datenbank verwenden dieselben
  konfigurierbaren Zugangsdaten.

## 6. Frontend, API-Pfade und Bedienung

- Die Frontend-Services verwenden eine zentrale API-Konfiguration statt
  verstreuter oder fest verdrahteter URLs.
- Authentifizierung, statische Avatar- und Item-URLs sowie mehrere
  Service-Aufrufe wurden an Entwicklungs- und Produktionsbetrieb angepasst.
- Learn-, Chat-, Dokument-, Profil-, Shop-, Inventar- und Social-Ansichten
  erhielten responsive und funktionale Korrekturen aus dem Produktionszweig.


## 7. Sicherheit und Robustheit

- Aufgaben und Dokumente werden vor Verwendung im Agentenkontext dem
  angemeldeten Nutzer zugeordnet.
- Toolnamen werden sowohl bei der Planung als auch unmittelbar vor der
  Ausführung gegen den Capability-Scope geprüft.
- Modellfehler, ungültiges JSON, fehlerhafte Toolargumente und fehlgeschlagene
  Tools werden in definierte Fallbacks oder Toolbeobachtungen überführt.


## Bewusst verbleibende Grenzen

- Das MAS arbeitet seriell und innerhalb eines Backend-Prozesses. Es ist kein
  verteiltes System mit unabhängigen Agentendiensten.
- Agentenzustände und turn-lokale Toolbeobachtungen werden noch nicht als
  langfristiges Episodengedächtnis gespeichert.
- Schreibende Tools werden vor dem Reviewer ausgeführt und können durch dessen
  Kritik nicht zurückgerollt werden.
- Lernprofil-Update und Belohnung sind im `evaluate`-Scope erlaubt, ihre
  Reihenfolge und die Herkunft des Scores werden aber noch nicht durch einen
  serverseitigen Zustandsautomaten erzwungen.
- Die Produktionswerte `postgres/postgres` sind weiterhin Compose-Defaults und
  müssen bei einem realen Deployment explizit durch sichere, URL-kodierte
  Zugangsdaten ersetzt werden.
- Die Tests belegen Kontrollfluss und technische Integration, nicht die
  pädagogische Wirksamkeit oder die Qualität beliebiger Modellantworten.
