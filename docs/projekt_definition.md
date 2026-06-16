# Übungsblatt 01 – Projektdefinition & Agentenanalyse

## Projektname

**StudyMummy – Agentic AI Learning Platform**

## 1. Elevator Pitch

StudyMummy ist eine KI-gestützte Lernplattform für Schüler, Studierende, Auszubildende und Selbstlerner. Nutzer können Aufgabenblätter, PDFs, Screenshots oder andere Lernmaterialien hochladen und werden anschließend von einem intelligenten Tutor-Agenten Schritt für Schritt beim Verstehen und Lösen der Aufgaben unterstützt.

Im Gegensatz zu einem normalen Chatbot gibt StudyMummy nicht einfach sofort die Lösung aus. Der Agent analysiert die Aufgaben, erkennt Themen und Schwierigkeiten, stellt gezielte sokratische Fragen, bewertet Antworten, passt Hilfestellungen an den Lernstand an und entscheidet, wann Wiederholung oder ein Lernspiel sinnvoll ist. Zusätzlich erstellt StudyMummy am Ende einer Lerneinheit ein persönliches Cheatsheet und belohnt Lernfortschritt durch virtuelle Währung.

---

## 2. PEAS-Analyse

| PEAS-Komponente | Beschreibung für StudyMummy |
|---|---|
| **Performance Measure** | Erfolg erkennt man daran, dass Nutzer Aufgaben besser verstehen, Aufgaben korrekt lösen, weniger wiederholte Fehler machen, Schwächen gezielt verbessern und motiviert weiterlernen. Weitere Messgrößen sind gelöste Aufgaben, korrekte Antworten, Verbesserung des Confidence-Scores pro Thema, erfolgreich abgeschlossene Lernspiele, sinnvolle Cheatsheets und Nutzerzufriedenheit. |
| **Environment** | Die Umgebung besteht aus der Lernplattform, den hochgeladenen Lernmaterialien, den einzelnen Aufgaben, dem aktuellen Lernstand des Nutzers, den Interaktionen im Chat, den generierten Spielen, dem Game Tab und dem persönlichen Fortschrittsprofil. Außerdem gehören verschiedene Fächer wie Mathematik, Informatik, Englisch oder Naturwissenschaften zur Umgebung. |
| **Actuators** | Der Agent kann Aufgaben strukturieren, Hinweise geben, Rückfragen stellen, Erklärungen erzeugen, Antworten bewerten, Fehler markieren, Lernfortschritt aktualisieren, Wiederholungen empfehlen, Lernspiele starten, Quizfragen generieren, virtuelle Währung vergeben und Cheatsheets erstellen. |
| **Sensors** | Der Agent erhält Eingaben durch hochgeladene PDFs, Screenshots, Fotos, Word-Dokumente, Textaufgaben, Nutzerantworten, Chatnachrichten, ausgewählte Fächer, Aufgabenstatus, bisherige Fehler, Lernhistorie, Confidence-Werte und Spielergebnisse. |

---

## 3. Umgebungseigenschaften

| Dimension | Einordnung | Begründung |
|---|---|---|
| **Fully / Partially Observable** | **Partially observable** | Der Agent sieht zwar hochgeladene Aufgaben, Chatantworten und gespeicherte Lernfortschritte, aber er kennt nicht vollständig den tatsächlichen Wissensstand, die Motivation oder das Verständnis des Nutzers. Diese müssen aus den Antworten und Fehlern geschätzt werden. |
| **Deterministic / Stochastic** | **Stochastic** | Gleiche Aufgaben können bei verschiedenen Nutzern zu unterschiedlichen Antworten, Fehlern und Lernverläufen führen. Außerdem können LLM-Antworten variieren. Der Agent arbeitet daher mit Unsicherheit. |
| **Episodic / Sequential** | **Sequential** | Jede Interaktion beeinflusst spätere Entscheidungen. Wenn ein Nutzer zum Beispiel mehrfach Fehler bei linearen Funktionen macht, beeinflusst das zukünftige Hinweise, Wiederholungen, Quizfragen und Cheatsheet-Inhalte. |
| **Static / Dynamic** | **Dynamic** | Die Umgebung verändert sich während der Nutzung: Aufgabenstatus wechseln von „Open“ zu „Solved“ oder „Repeat“, Confidence-Werte verändern sich, neue Fehler werden erkannt und Spiele können neue Lernstände erzeugen. |
| **Discrete / Continuous** | **Überwiegend discrete, teilweise continuous** | Viele Elemente sind diskret, zum Beispiel Aufgaben, Antwortversuche, Statuswerte, Spielrunden und Quizfragen. Gleichzeitig gibt es kontinuierliche bzw. graduelle Werte wie Confidence-Scores, Fortschrittswerte oder Schwierigkeitsanpassungen. |
| **Single-Agent / Multi-Agent** | **Konzeptionell Multi-Agent, MVP eher orchestrierter Single-Agent** | Die Idee enthält mehrere spezialisierte Rollen wie Upload Analyzer Agent, Tutor Agent, Evaluation Agent, Learning Profile Agent, Progress Agent, Game Generator Agent und Cheatsheet Agent. Für das MVP kann dies zunächst als ein zentraler Agent mit mehreren Funktionen umgesetzt werden. |
| **Known / Unknown** | **Partially unknown** | Die grundlegenden Regeln der Plattform sind bekannt, zum Beispiel Upload, Aufgabenanalyse, Tutor-Chat und Quiz. Unbekannt sind jedoch die konkreten Inhalte der hochgeladenen Aufgaben, die Qualität der Nutzerantworten, individuelle Wissenslücken und mögliche Missverständnisse. |

---

## 4. Agententyp

StudyMummy kommt am nächsten an einen **Learning Agent** heran.

StudyMummy besitzt Merkmale mehrerer Agententypen:

| Agententyp | Bezug zu StudyMummy |
|---|---|
| **Simple Reflex Agent** | Teilweise bei einfachen Regeln, z. B. wenn eine Antwort leer ist, fordert der Agent eine neue Eingabe an. |
| **Model-Based Agent** | Der Agent nutzt ein internes Modell über Aufgabenstatus, Themen, Schwächen und Lernfortschritt. |
| **Goal-Based Agent** | Das Ziel ist, dass der Nutzer Aufgaben versteht, korrekt löst und Schwächen verbessert. |
| **Utility-Based Agent** | Der Agent kann zwischen verschiedenen nächsten Aktionen abwägen, z. B. weiterer Hinweis, neue Aufgabe, Wiederholung oder Spielmodus. |
| **Learning Agent** | Der Agent aktualisiert das Lernprofil anhand von Nutzerantworten und passt zukünftige Hilfen, Wiederholungen, Spiele und Cheatsheets daran an. |

**Begründung:**  
StudyMummy ist ein Learning Agent, weil das System nicht nur einzelne Antworten erzeugt, sondern aus Nutzerinteraktionen ein Lernprofil ableitet. Dieses Profil beeinflusst spätere Entscheidungen, zum Beispiel welches Hilfeniveau gewählt wird, welche Themen wiederholt werden sollen, welche Quizfragen generiert werden und welche Inhalte im Cheatsheet besonders hervorgehoben werden.

---

# AUFGABE 2

---
# Übungsblatt 02 - Architekturentwurf: Die kognitiven Schichten

**Projektname:** StudyMummy - Agentic AI Learning Platform

**Leitfrage:** Wie nimmt StudyMummy die Welt wahr, was merkt sich der Agent, und wie entscheidet er?

StudyMummy ist eine KI-gestützte Lernplattform, bei der Nutzer Lernmaterialien hochladen und anschließend durch einen sokratischen Tutor-Agenten beim Verstehen und Lösen der Aufgaben unterstützt werden. Für den Architekturentwurf wird StudyMummy anhand der vier kognitiven Schichten Perception, Memory, Planning und Action betrachtet.

---

## 1. Schichten-Mapping

### 1.1 Perception - Wahrnehmung

Die Perception-Schicht ist dafür zuständig, alle relevanten Eingaben des Nutzers und der Plattform aufzunehmen und für die weitere Verarbeitung vorzubereiten.

#### Inputs

| Input                        | Beschreibung                                                        |
|-----------------------------|---------------------------------------------------------------------|
| PDF-Dateien                 | Hochgeladene Aufgabenblätter, Skripte oder Lernmaterialien         |
| Screenshots / Fotos         | Bilder von Aufgaben, Tafelbildern oder handschriftlichen Notizen   |
| Textdokumente / Word-Dateien| Strukturierte oder unstrukturierte Lernunterlagen                  |
| Direkte Texteingaben        | Antworten des Nutzers, Rückfragen, Notizen                         |
| Fachauswahl                 | Auswahl eines Fachs, z. B. Mathematik, Informatik oder Englisch    |
| Nutzerinteraktionen         | Klicks auf Aufgaben, Start eines Spiels, Auswahl eines Hilfeniveaus|
| Lernverlaufsdaten           | Bereits gelöste Aufgaben, falsche Antworten, Spielresultate        |

#### Vorverarbeitung

- Textextraktion aus PDFs
- OCR für Screenshots und Fotos
- Aufteilung des Materials in einzelne Aufgaben
- Erkennung von Fach, Thema und Schwierigkeit
- Extraktion wichtiger Formeln, Begriffe und Methoden
- Umwandlung der Inhalte in ein strukturiertes Aufgabenformat
- Erkennung des aktuellen Aufgabenstatus
- Normalisierung von Nutzerantworten für die Bewertung

---

### 1.2 Memory - Gedächtnis

#### Working Memory / Kurzzeitgedächtnis

| Inhalt                  | Beispiel                                                    |
|------------------------|-------------------------------------------------------------|
| Aktuelle Aufgabe       | Der Nutzer bearbeitet Aufgabe 2 zu linearen Funktionen      |
| Aktuelle Nutzerantwort | „x = 1.5"                                                   |
| Aktuelles Hilfeniveau  | Level 2: spezifische Hilfestellung                          |
| Aktueller Dialogverlauf| Bisherige Fragen und Antworten innerhalb der Aufgabe        |
| Zwischenschritte       | Bisher erkannte Rechenwege oder Fehler                      |

#### Episodic Memory / Ereignisgedächtnis

| Inhalt               | Beispiel                                                    |
|---------------------|-------------------------------------------------------------|
| Bearbeitete Aufgaben| Aufgabe 1 wurde gelöst, Aufgabe 2 war fehlerhaft            |
| Fehlerhistorie      | Der Nutzer macht wiederholt Vorzeichenfehler                |
| Spielverlauf        | Quiz Show Runde mit 3 von 5 richtigen Antworten             |
| Tutorverlauf        | Bei Gleichungen wurde mehrfach Hilfestufe 3 benötigt        |
| Session-Historie    | Letzte Sitzung: Thema „quadratische Funktionen"             |

#### Semantic Memory / Wissensgedächtnis

| Inhalt             | Beispiel                                                        |
|-------------------|-----------------------------------------------------------------|
| Fachwissen        | Mathematische Regeln, Grammatikregeln, Programmierkonzepte      |
| Formeln           | f(x) = mx + b, pq-Formel, Ohmsches Gesetz                       |
| Methoden          | Gleichungen umstellen, Textanalyse, Debugging                   |
| Aufgabentypen     | Nullstellen bestimmen, Code erklären, Vokabeln abfragen         |
| Erklärstrategien  | Sokratische Fragen, Beispiele, typische Fehler                  |

#### Wo reicht das Context Window?

Das Context Window reicht für:
- einzelne kurze Aufgaben
- den aktuellen Chatverlauf
- direkte Rückfragen
- kurze Erklärungen
- einfache Quizrunden

Es reicht **nicht** für:
- vollständige Lernhistorien über mehrere Sitzungen
- langfristige Schwächenanalyse
- viele hochgeladene Dokumente / große PDFs
- Wiederholung alter Fehler
- personalisierte Cheatsheets über mehrere Themen hinweg

---

### 1.3 Planning - Planung und Entscheidung

#### Reaktive Entscheidungen

| Situation                         | Reaktion                                                    |
|----------------------------------|-------------------------------------------------------------|
| Nutzer gibt keine Antwort        | Agent fragt nach oder gibt einen kleinen Hinweis            |
| Antwort ist offensichtlich falsch| Agent gibt Feedback und eine Hilfestellung                  |
| Nutzer fragt nach Lösung         | Agent gibt zunächst einen Hinweis statt direkt die Lösung   |
| Aufgabe wurde gelöst             | Status wird auf „solved" gesetzt                            |
| Nutzer wählt Game Tab            | Quizmodus wird gestartet                                    |

#### Deliberative Entscheidungen

| Entscheidung                              | Benötigte Informationen                                 |
|------------------------------------------|---------------------------------------------------------|
| Welches Hilfeniveau ist passend?         | Aufgabe, Fehlerhistorie, bisherige Antworten            |
| Soll die Aufgabe wiederholt werden?      | Anzahl Fehler, Confidence-Wert, Schwierigkeit           |
| Soll ein Lernspiel vorgeschlagen werden? | Lernphase, Motivation, Fehlerhäufigkeit                 |
| Welche Quizfragen sollen generiert werden?| Schwächen, Themen, bisherige Aufgaben                  |
| Was gehört ins Cheatsheet?               | Gelöste Aufgaben, typische Fehler, zentrale Konzepte    |
| Welche Aufgabe sollte als Nächstes kommen?| Reihenfolge, Schwierigkeit, Lernstand                  |

#### Braucht StudyMummy hierarchische Pläne?

Ja, zumindest einfache hierarchische Pläne sind sinnvoll.

**Beispiel für einen hierarchischen Lernplan:**

1. Arbeitsblatt analysieren
2. Aufgaben strukturieren
3. Aufgabe auswählen
4. Nutzer durch Aufgabe führen
5. Antwort bewerten
6. Lernprofil aktualisieren
7. Entscheiden: nächste Aufgabe, Wiederholung, Lernspiel oder Cheatsheet
8. Am Ende Zusammenfassung erzeugen

Innerhalb einer einzelnen Aufgabe kann der Tutor-Agent zusätzlich einen kleineren Plan verfolgen: Aufgabenverständnis prüfen, relevante Formel oder Methode erfragen, ersten Lösungsschritt begleiten, Zwischenergebnis prüfen, Endergebnis bewerten und Fehler erklären oder Aufgabe abschließen.

---

### 1.4 Action - Handlung

| Aktion                      | Beschreibung                                                                  |
|----------------------------|-------------------------------------------------------------------------------|
| Aufgaben extrahieren       | Der Agent strukturiert das hochgeladene Material in einzelne Aufgaben         |
| Aufgaben klassifizieren    | Fach, Thema, Schwierigkeit und benötigte Konzepte werden erkannt              |
| Sokratische Fragen stellen | Der Agent stellt gezielte Rückfragen statt direkt die Lösung zu geben         |
| Hinweise geben             | Je nach Hilfeniveau gibt der Agent kleine oder konkrete Hilfen                |
| Antworten bewerten         | Nutzerantworten werden als korrekt, teilweise korrekt oder falsch bewertet    |
| Fehler erklären            | Der Agent erkennt typische Fehler und erklärt sie verständlich                |
| Lernprofil aktualisieren   | Confidence-Werte und Schwächen werden gespeichert                             |
| Aufgabenstatus ändern      | Aufgaben werden auf „open", „in progress", „solved", „repeat" usw. gesetzt   |
| Lernspiel generieren       | Der Agent erstellt Quizfragen passend zum aktuellen Lernstand                 |
| Virtuelle Währung vergeben | Nutzer erhalten Belohnungen für richtige Antworten oder abgeschlossene Spiele |
| Cheatsheet erstellen       | Der Agent erzeugt eine persönliche Zusammenfassung nach der Lerneinheit       |

#### Aktionen mit Seiteneffekten

| Aktion                      | Seiteneffekt                                              |
|----------------------------|-----------------------------------------------------------|
| Lernprofil aktualisieren   | Dauerhafte Veränderung des Nutzerprofils                  |
| Virtuelle Währung vergeben | Veränderung des Kontostands innerhalb der Plattform       |
| Aufgabenstatus ändern      | Veränderung des Fortschritts im Arbeitsblatt              |
| Cheatsheet speichern       | Neues dauerhaftes Dokument entsteht                       |
| Spielhistorie speichern    | Fortschritt im Game Tab verändert sich                    |
| Joker kaufen oder einsetzen| Virtuelle Währung und Spielzustand verändern sich         |

---

## 2. Architekturdiagramm

<img width="864" height="1821" alt="architekturdiagram" src="https://github.com/user-attachments/assets/dcc1c3b7-4cfe-4298-8d5e-2c2273f04f69" />

---

## 3. Kritische Schichten und größte Herausforderungen

### Kritische Schicht 1: Perception

- Aufgaben korrekt voneinander trennen
- Handschriftliche oder schlecht lesbare Inhalte erkennen
- Fach und Thema zuverlässig bestimmen
- Formeln korrekt extrahieren
- Tabellen, Diagramme oder Bilder interpretieren

### Kritische Schicht 2: Memory

- Sinnvolle Confidence-Werte berechnen
- Alte Fehler nicht vergessen
- Irrelevante Informationen nicht dauerhaft speichern
- Aktuelle Aufgabe und langfristigen Lernstand sauber trennen
- Lernprofil über mehrere Sitzungen hinweg konsistent halten

### Kritische Schicht 3: Planning

- Nicht zu schnell die Lösung verraten
- Passende Hilfestufe wählen
- Sinnvolle Wiederholungen vorschlagen
- Lernspiele nicht zu früh oder zu spät starten
- Zwischen Motivation und echtem Lernen balancieren
- Game-Mechaniken nicht wichtiger machen als Lernfortschritt

---

## 4. Identifizierte Schwäche im Entwurf

**Die aktuell schwächste Schicht ist Perception, besonders bei komplexen oder schlecht strukturierten Uploads.**

StudyMummy hängt stark davon ab, dass hochgeladene Materialien korrekt verstanden werden. Bei klaren Text-PDFs ist das relativ gut lösbar. Schwieriger wird es bei:

- Fotos von Arbeitsblättern
- Handschriftlichen Notizen
- Mathematischen Formeln
- Mehrspaltigen PDFs
- Diagrammen und Tabellen
- Aufgaben mit mehreren Teilaufgaben
- Unklaren Aufgabenstellungen

Wenn der Agent bereits bei der Extraktion Fehler macht, können alle weiteren Schichten falsche Entscheidungen treffen. Eine falsch erkannte Aufgabe führt zu falscher Tutorunterstützung, falschen Quizfragen und einem unbrauchbaren Cheatsheet.

### Was fehlt noch?

- Validierung der erkannten Aufgaben
- Möglichkeit für Nutzer, erkannte Aufgaben zu korrigieren
- Konfidenzwerte für die Extraktion
- Vorschau der erkannten Aufgaben vor dem Start
- Manuelle Nachbearbeitung von Thema, Fach und Schwierigkeit
- Bessere Unterstützung für Formeln und handschriftliche Inhalte

---

## 5. Technologie-Vorauswahl

| Schicht / Baustein                   | Mögliche Technologie                                              |
|-------------------------------------|-------------------------------------------------------------------|
| Perception: PDF-Upload              | Frontend mit File Upload                                      |
| Perception: PDF-Textextraktion      | PyMuPDF, pdfplumber oder LangChain Document Loader               |
| Perception: OCR für Bilder          | Tesseract OCR, Google Vision API oder visionfähiges LLM          |
| Perception: Dokumentanalyse         | LLM mit Structured Output                                         |
| Perception: Aufgabenstrukturierung  | JSON Schema / Pydantic Models                                     |
| Memory: Working Memory              | LLM Context Window / Session State                               |
| Memory: Nutzerprofil                | PostgreSQL, Firebase Firestore oder Supabase                     |
| Memory: Semantic Memory             | Vector Store, z. B. Chroma, FAISS oder pgvector                  |
| Planning: Agenten-Orchestrierung    | LangGraph oder eigener Orchestrator                              |
| Planning: Entscheidungslogik        | Kombination aus Regeln und LLM-Entscheidungen                    |
| Planning: Structured Decisions      | JSON Output / Function Calling                                    |
| Action: Tutorantworten              | LLM API                                                           |
| Action: Antwortbewertung            | LLM + Regelprüfungen                                             |
| Action: Quizgenerierung             | LLM mit JSON Schema                                               |
| Action: Cheatsheet-Erstellung       | LLM + gespeicherte Sessiondaten                                  |
| Action: virtuelle Währung           | Backend-Service mit Datenbankupdate                              |
| Frontend                            | Flutter                                                          |
| Backend                             | FastAPI                                                          |
| Authentifizierung                   | Firebase Auth, Supabase Auth oder Auth.js                        |
| Dateiablage                         | Supabase Storage, Firebase Storage oder S3                       |
| Deployment                          | Vercel für Frontend, Render/Fly.io/Railway für Backend           |

---

## 6. Offene Fragen für den nächsten Termin: LLMs, RAG & Tool Use

| Bereich           | Offene Fragen                                                                                                                              |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Structured Output| Wie erzwingen wir zuverlässige JSON-Ausgaben für Aufgabenanalyse, Quizfragen und Cheatsheets? Wie gehen wir mit ungültigen LLM-Antworten um? |
| RAG              | Welche Inhalte sollen in einen Vector Store? Nur hochgeladene Materialien oder auch allgemeine Lerninhalte?                                |
| Tool Use         | Welche Tools braucht der Agent zuerst? Mögliche Tools: `extract_tasks_from_document`, `evaluate_answer`, `update_learning_profile`, `generate_quiz_questions`, `create_cheatsheet` |
| Memory           | Wie werden Confidence-Werte berechnet? Wie lange sollen Lernverläufe gespeichert werden?                                                  |
| Sicherheit       | Wie verhindern wir, dass der Agent sofort komplette Lösungen ausgibt, obwohl sokratisches Lernen gewünscht ist?                           |
| MVP-Einschränkung| Starten wir zuerst nur mit Mathematik? Unterstützen wir zuerst nur Text/PDF statt Fotos und Handschrift?                                 |
