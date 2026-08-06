# Warum StudyMummy ein agentisches System ist

## Arbeitsdefinition

Ein Softwaresystem wird hier als agentisch betrachtet, wenn es einen Zustand seiner Umgebung wahrnimmt, ein Ziel verfolgt, selbstständig eine nächste Aktion auswählt, Werkzeuge zur Veränderung der Umgebung einsetzen kann und die Wirkung vor oder nach der Ausgabe überprüft.

StudyMummy erfüllt diese Kriterien nicht nur durch Prompttexte, sondern durch ausführbaren Programmcode und explizite Datenverträge.

## Nachweisbare Eigenschaften

### Zielgerichtetes Verhalten

Das übergeordnete Ziel ist nicht bloß die Erzeugung einer Antwort. Der nächste Schritt soll Verständnis fördern und zur aktuellen Hilfestufe passen. Der Planning Agent übersetzt dieses Ziel in ein beobachtbares Turn-Ziel und Erfolgskriterien.

### Zustandsbezug

Entscheidungen berücksichtigen Sitzung, Aufgabe, Hilfestufe, Dialoghistorie, Dokumentwissen und Lernprofil. Gleiche Nachrichten können dadurch in verschiedenen Zuständen zu unterschiedlichen Plänen führen.

### Autonome Aktionsauswahl

Der Planning Agent klassifiziert die Absicht und wählt zwischen sokratischer Frage, Hinweis, Erklärung, Bewertung, Lernplan, Terminaktion oder Klärung. Die API legt diese Aktion nicht fest.

### Werkzeuggebrauch

Der Tutor kann registrierte Werkzeuge verwenden, beispielsweise zur Antwortbewertung, Belohnung oder Terminverwaltung. Werkzeuge besitzen strukturierte Schemas und werden vom System ausgeführt; sie sind keine behaupteten Textaktionen.

### Begrenzte Agency

Autonomie bedeutet nicht unbegrenzte Rechte. Eine feste Capability-Policy schränkt Werkzeuge anhand der geplanten Aktion ein. Identität und Nutzerkontext werden durch die Anwendung gebunden. Das Modell kann den Scope nicht selbst erweitern.

### Reflexion und Qualitätskontrolle

Ein separater Reviewer bewertet das Ergebnis gegen den Plan und die Tutorprinzipien. Er kann eine Antwort ablehnen und ersetzen. Planung und Review sind dadurch nicht nur Abschnitte desselben freien Prompts, sondern getrennte Rollen mit typisierten Ergebnissen.

### Beobachtbarkeit

Jeder Lauf liefert einen kompakten Trace aus Phasen, Agenten, Zusammenfassungen und Laufzeiten. Zusätzlich enthält die Antwort den strukturierten Plan und die tatsächlich ausgeführten Tools.

## Multi-Agent-Einordnung

StudyMummy ist ein orchestriertes, hierarchisches Multi-Agent-System:

- Der **Planning Agent** entscheidet, was als Nächstes geschehen soll.
- Der **Tutor Agent** führt diese Entscheidung aus und interagiert mit Tools.
- Der **Reviewer Agent** besitzt ein unabhängiges Kontrollziel.
- Der **Orchestrator** kontrolliert Reihenfolge, Datenfluss und Abbruchbedingungen.

Die Rollen teilen sich denselben LLM-Adapter, besitzen aber unterschiedliche Ziele, Systemanweisungen, Ausgabeprotokolle und Rechte. Diese logische Agententrennung ist für ein Softwaresystem entscheidender als die Verwendung verschiedener Modellanbieter.

## Abgrenzung zu einem normalen Chatbot

| Merkmal | Einfacher Chatbot | StudyMummy |
|---|---|---|
| Zustand | primär Chatfenster | persistente Session, Aufgabe, Lernprofil und RAG |
| Entscheidung | direkte Textgenerierung | strukturierter Plan vor der Ausführung |
| Aktionen | Textantwort | kontrollierte Tools mit Side Effects |
| Kontrolle | häufig keine | unabhängiger Reviewer |
| Rechte | alle angebotenen Tools | aktionsabhängiger Capability-Scope |
| Nachvollziehbarkeit | Antworttext | Plan, Tools, Rollen und Trace |
| Ausfallverhalten | Modellfehler | deterministische Planungs- und Sicherheits-Fallbacks |

## Grenzen

Das System besitzt begrenzte Turn-Autonomie. Es verfolgt derzeit keine dauerhaft laufenden Ziele außerhalb einer Nutzerinteraktion und verändert keine externen Systeme ohne einen konkreten Chat-Turn. Diese Begrenzung ist für eine Lernplattform beabsichtigt: Sie erhöht Kontrollierbarkeit, Datenschutz und Reproduzierbarkeit.

Für empirische Aussagen in einer Hausarbeit sollten Agentenläufe mit festen Testsätzen verglichen werden. Geeignete Metriken sind Planerfüllung, fachliche Korrektheit, Hilfestufen-Adhärenz, Toolpräzision, Revisionsrate, Latenz und Lernfortschritt über mehrere Sitzungen.
