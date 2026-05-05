# Übungsblatt 1 | Agentic AI WP | Thomas Clemen

**Gruppe 2 – Nicola Ye, Frithjof Beims, David Grigutsch, Colvin Sowa, Jannis Martensen, Sebastian Hauschild**

## Elevatorpitch für StudyMummy

StudyMummy ist ein proaktiver KI-Mentor, der Schüler nicht durch das bloße Vorsagen von Lösungen, sondern durch gezielte sokratische Fragen und adaptive Hilfestellungen zum eigenständigen Lernerfolg führt. Dank Agentic AI erkennt die App individuelle Wissenslücken in Echtzeit, passt ihre Erklärstrategie dynamisch an den Lernfortschritt an und festigt das Verständnis durch maßgeschneiderte Transferaufgaben. So wird aus passivem Abschreiben aktives Begreifen, das sich exakt am Tempo und den Bedürfnissen des Lernenden orientiert.

## 1. PEAS-Analyse

| Komponente | Beschreibung für StudyMummy |
|---|---|
| **Performance Measure (Erfolg)** | - Lernfortschritt: Korrekte Beantwortung von Transferaufgaben durch den Schüler.<br>- Verständnis-Rate: Weniger Rückfragen bei ähnlichen Problemen.<br>- Engagement: Zeit, die der Schüler aktiv mit dem Tutor verbringt.<br>- Effizienz: Minimale Anzahl an Hinweisen bis zur selbstständigen Lösung. |
| **Environment (Umgebung)** | - Das Interface der App (Chat/Whiteboard).<br>- Die digitale Wissensdatenbank (Lehrpläne, Fachwissen).<br>- Der aktuelle kognitive Zustand des Schülers (indirekt). |
| **Actuators (Aktoren)** | - Textausgabe: Sokratische Fragen, Erklärungen, Lob/Motivation.<br>- Inhaltserstellung: Generierung von Übungsaufgaben oder Grafiken.<br>- UI-Elemente: Markierungen auf dem virtuellen Whiteboard setzen. |
| **Sensors (Sensoren)** | - Vision: Kamera/Upload von Aufgaben (Texterkennung/OCR).<br>- Text-Input: Antworten und Fragen des Schülers im Chat.<br>- Metadaten: Antwortzeit, Korrekturhäufigkeit des Schülers, Tippverhalten. |

## 2. Umgebungseigenschaften (7 Dimensionen)

**Wie komplex ist die Welt, in der StudyMummy arbeitet?**

1. **Partially Observable:** Der Agent sieht zwar die Aufgabe, aber nicht direkt in den Kopf des Schülers. Er muss den Wissensstand aus den Antworten erschließen.
2. **Stochastic:** Die Reaktion des Schülers ist nicht zu 100% vorhersagbar. Auf dieselbe Frage können völlig unterschiedliche Antworten folgen.
3. **Sequential:** Eine Antwort baut auf der vorherigen auf. Die Entscheidung, jetzt einen Tipp zu geben, beeinflusst, wie der Schüler die nächste Aufgabe versteht.
4. **Dynamic:** Die Umgebung ist technisch gesehen static, während die KI nachdenkt, aber dynamic im Sinne des Lernprozesses: Die Frustration oder Aufmerksamkeit des Schülers ändert sich über die Zeit.
5. **Discrete:** Die Interaktion findet in abgeschlossenen Schritten statt (Nachricht schicken, Aufgabe lösen, Feedback erhalten).
6. **Multi-Agent:** Es gibt mindestens zwei Agenten: Die KI (Tutor) und den Menschen (Schüler), deren Ziele (Lernen vs. schnelle Lösung) manchmal konkurrieren.
7. **Known:** Die Regeln der Fachbereiche (z. B. Mathematik oder Grammatik) sind dem System bekannt und fest definiert.

## 3. Agententyp: Learning Agent

StudyMummy kommt dem **Learning Agent** am nächsten.

**Begründung:**

- **Performance Element:** Er fungiert als Tutor und gibt Hinweise (das operative Geschäft).
- **Critic:** Er vergleicht die Antwort des Schülers mit der Ideallösung und bewertet, ob der aktuelle Lehransatz funktioniert.
- **Learning Element:** Der Agent lernt über die Zeit, welche Erklärungen oder Analogien bei diesem spezifischen Schüler am besten funktionieren (Personalisierung).
- **Problem Generator:** Er erstellt proaktiv neue Aufgaben, um Wissenslücken zu testen und das System „herauszufordern“, damit der Schüler nicht nur auswendig lernt.
