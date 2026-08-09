# Änderungen gegenüber dem ursprünglichen Projekt

Das ursprünglich geforkte StudyMummy-Projekt wurde strukturell, technisch und funktional überarbeitet. Die wichtigsten Anpassungen sind:

- **Bereinigung der Projektstruktur:** Alte Aufgabenstellungen, Musterlösungen, Präsentationen und weitere nicht mehr benötigte Projektdateien wurden entfernt. Die verbleibende Struktur wurde übersichtlicher aufgebaut und die Dokumentation aktualisiert.

- **Einführung einer agentischen Architektur:** Der bisherige Tutor wurde zu einem nachvollziehbaren Multi-Agent-System erweitert. Ein Planning Agent plant den nächsten Lernschritt, ein Tutor Agent führt ihn aus und ein Reviewer Agent kontrolliert die erzeugte Antwort. Wahrnehmung, Gedächtnis und Werkzeugzugriffe sind als weitere klar abgegrenzte Bestandteile in den Ablauf integriert.

- **Kontrollierte Werkzeugnutzung:** Die Agenten können registrierte Werkzeuge beispielsweise zur Antwortbewertung, Aktualisierung des Lernprofils oder Terminverwaltung verwenden. Die verfügbaren Werkzeuge werden abhängig von der geplanten Aktion begrenzt, damit keine unpassenden oder unerlaubten Aktionen ausgeführt werden.

- **Verbesserter Lernkontext:** Im Learning-Tab erhält der Tutor den konkreten Kontext der ausgewählten Aufgabe sowie des aktuell geöffneten Dokuments. Die RAG-Suche wird auf das relevante Dokument eingeschränkt, wodurch Rückfragen und Hilfestellungen gezielter auf die Lerninhalte eingehen können.

- **Persistenz und Nachvollziehbarkeit:** Sitzungsverlauf, aktive Aufgabe, Hilfestufe und Lernprofil werden in den Agentenablauf einbezogen. Zusätzlich werden Agentenentscheidungen und beteiligte Rollen als kompakter Trace erfasst, ohne interne Gedankengänge offenzulegen.

- **Technische Fehlerbehebungen:** Die OpenAI-Anbindung wurde mit unterschiedlichen Modellfamilien kompatibel gemacht. Außerdem wurden API-Pfade, statische Asset-URLs, Authentifizierung und verschiedene Frontend-Integrationen vereinheitlicht und robuster umgesetzt.

- **Frontend- und Betriebsverbesserungen:** Das responsive Verhalten mehrerer Ansichten, der Dokument-Upload und verschiedene UI-Komponenten wurden verbessert. Das Docker-Setup unterstützt getrennte Entwicklungs- und Produktionsprofile; für den Produktivbetrieb wurden zusätzlich Nginx- und Deployment-Konfigurationen integriert.

- **Dokumentation und Qualitätssicherung:** Die Systemarchitektur und der agentische Ablauf wurden gesondert dokumentiert. Ergänzende Backend- und Frontend-Tests sichern unter anderem die Orchestrierung, Modellkompatibilität und Übergabe des Aufgabenkontexts ab.
