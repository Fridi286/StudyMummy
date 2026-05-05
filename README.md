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
