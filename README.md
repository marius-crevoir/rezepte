# Unsere Küche

Eine kleine, mobile und installierbare Rezept-Web-App mit Suche, lokalen Favoriten, Portionsrechner und offizieller Bring!-Integration. **Keine Datenbank, kein CMS, keine laufenden Hostingkosten für ein öffentliches GitHub-Pages-Repository.**

## Einmalig veröffentlichen

1. Auf GitHub ein **öffentliches** Repository `rezepte` unter `marius-crevoir` erstellen, mit einem README initialisieren. Alternativ diesen Projektordner als vollständiges neues Repository hochladen.
2. Die Projektdateien in den `main`-Branch legen.
3. Im Repository `Settings → Pages → Build and deployment → Source → GitHub Actions` wählen.
4. Unter `Actions` den Workflow **Unsere Küche veröffentlichen** starten (oder auf einen Push warten).
5. Erwartete URL: <https://marius-crevoir.github.io/rezepte/>. Erst nach erfolgreichem Deployment live.

GitHub-Repository und Pages-Einstellungen können bei der aktuellen Integration nicht automatisch angelegt/konfiguriert werden. Sobald `rezepte` existiert, kann ChatGPT über den verbundenen GitHub-Zugang Dateien hinzufügen oder bearbeiten.

## Ein Rezept hinzufügen

1. Eine Datei `content/recipes/<slug>.json` anlegen. Als Vorlage eines der drei Beispielrezepte verwenden.
2. `slug` muss aus Kleinbuchstaben, Zahlen und Bindestrichen bestehen und zum Dateinamen passen.
3. Für jedes Rezept Titel, Beschreibung, Autor, Zutaten (Menge, Einheit, Name), Schritte, Bild und Portionenzahl ausfüllen. Mengen müssen Zahlen sein oder `null` für "nach Geschmack".
4. Datei auf `main` speichern. Die GitHub Action erzeugt automatisch `data/recipes.json` sowie die öffentliche Rezeptseite `rezepte/<slug>/` und veröffentlicht alles.

Das kann ChatGPT direkt über den verbundenen GitHub-Zugang übernehmen. So bleibt ChatGPT der Eingabekanal und GitHub das zuverlässige Archiv. Bilder gehören nach `assets/covers/` oder können mit einer öffentlich erreichbaren HTTPS-Adresse referenziert werden (Nutzungsrechte beachten).

Die drei Rezepte zu Beginn sind **Demorezepte** und können jederzeit entfernt oder ersetzt werden.

## Bring! – wichtige Details

Auf jeder Rezeptdetailseite und jeder Rezeptkarte gibt es einen sichtbaren Bring!-Import-Link. Dieser verwendet den von Bring! offiziell dokumentierten GET-Endpunkt `https://api.getbring.com/rest/bringrecipes/deeplink` und benötigt kein externes Widget-Skript. Jede Rezeptseite enthält bei Auslieferung bereits maschinenlesbares `schema.org/Recipe` JSON-LD mit **Name, Autor und Zutaten**. Das ist entscheidend, weil Bring! die öffentlich erreichbare Seite parst. Der Portionsrechner aktualisiert den Import-Link mit `baseQuantity` und `requestedQuantity`, damit Bring! die gewählte Menge berechnen kann. Ob Bring! die Werte tatsächlich korrekt übernimmt, muss in der App getestet werden. Nach Veröffentlichung kann jedes Rezept über <https://www.getbring.com/de/integration-prufen> auf Parser-Kompatibilität geprüft werden.

Der Bring!-Button kann auf lokalen Entwicklungsseiten ohne öffentlich abrufbare URL nicht vollständig getestet werden. Ein gemeinsamer Einkaufslisten-Import mehrerer Rezepte ist nicht implementiert.

## Lokal testen

```bash
python3 scripts/build.py
python3 -m http.server 8000
```

Danach <http://localhost:8000> öffnen. Über die Browser-Devtools lässt sich die mobile Ansicht testen. Der Service Worker funktioniert unter localhost oder HTTPS. Die Website läuft ohne externe JS-Bibliotheken; die Google Fonts sind optional und werden bei Offlinebetrieb durch Systemschrift ersetzt.

## Offline-Funktion und Synchronisierung

Website und Rezeptseiten werden vom Service Worker nach dem ersten Besuch zwischengespeichert. Neue Rezeptinhalte brauchen für die erste Synchronisierung eine Onlineverbindung. Favoriten liegen **nur im lokalen Browser** (`localStorage`), sie sind **nicht geräteübergreifend synchronisiert**. Es gibt noch keine gemeinsamen Wochenpläne, Benutzerkonten oder private Rezeptverwaltung. Alles, was öffentlich bei GitHub Pages liegt, kann auch von Fremden gelesen werden.

## Technik

- statisches HTML/CSS/JavaScript; kein npm oder Vite nötig
- Python-Generator für echte, crawlerlesbare Rezeptseiten
- Schema.org Recipe JSON-LD; Bring!-Import-Script
- PWA-Manifest und Service Worker
- GitHub Actions → GitHub Pages, automatischer Build bei Push auf `main`
- URL-Basis für strukturierte Daten via Umgebungsvariable `SITE_URL` konfigurierbar; Standard `https://marius-crevoir.github.io/rezepte/`
