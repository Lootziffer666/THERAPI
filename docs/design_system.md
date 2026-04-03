# therAPI Design System (Stitch-ready, v0)

Ziel: **Google Stitch** trotz eingeschränkter Befehlsgenauigkeit zuverlässig nutzen.

Dieses Dokument ist absichtlich in **kleinen, robusten Prompt-Bausteinen** aufgebaut (Atomic Prompts), damit Stitch weniger Interpretationsspielraum hat.

---

## 1) Produktkontext (für jeden Stitch-Startprompt)

> Baue ein Desktop-first Web-Interface für ein lokales API-Discovery-Tool namens **therAPI**. Fokus: HTTP-Capture, Endpoint-Übersicht, Schema-Versionen, Drift-Diff, OpenAPI-Export. Kein Marketing-Look, sondern Tooling-UI mit hoher Informationsdichte.

---

## 2) Design-Tokens (fix)

- **Theme:** dark-neutral
- **Border radius:** 10px
- **Spacing scale:** 4, 8, 12, 16, 24, 32
- **Font:** Inter (Semibold headings, Regular body)
- **Farben:**
  - bg `#0B1020`
  - panel `#121A2A`
  - panel-alt `#172238`
  - text `#E5ECF6`
  - text-muted `#9FB0C6`
  - accent `#56B6F7`
  - success `#46C37B`
  - warning `#F5A623`
  - danger `#E05D5D`
  - border `#253551`

---

## 3) Seitenstruktur (MVP)

1. **Control Panel**
2. **Endpoint Explorer**
3. **Schema Drift**
4. **Capture Inspector**
5. **OpenAPI Export**
6. **Collections Export**
7. **Settings**

---

## 4) Atomic Prompts für Stitch (empfohlen)

> Hinweis: Immer **nur 1 Prompt pro Schritt** senden. Erst Layout, dann Komponenten, dann States.

### 4.1 App Shell

**Prompt A1 — Grundlayout**

> Erzeuge eine Desktop-App-Shell mit linker Sidebar (240px), Topbar (56px), Content-Bereich rechts. Nutze dunkles Theme mit den angegebenen Tokens. Sidebar enthält Navigation: Control Panel, Endpoint Explorer, Schema Drift, Capture Inspector, OpenAPI Export, Collections Export, Settings.

**Prompt A2 — Topbar Status**

> Ergänze in der Topbar rechts drei Status-Chips: Proxy Status, Target Base URL, Capture Rate. Statusfarben: grün/gelb/rot je nach Zustand.

---

### 4.2 Control Panel

**Prompt C1 — Kartenlayout**

> Erzeuge im Content-Bereich ein 2-Spalten-Layout. Linke Spalte: Proxy Status Card und Capture Config Form. Rechte Spalte: Quick Actions Bar und Endpoint Overview Table.

**Prompt C2 — Proxy Status Card**

> Baue eine Karte "Proxy Status" mit Feldern: status, host, port, uptime und einem Refresh-Button.

**Prompt C3 — Capture Config Form**

> Baue ein Formular "Capture Config" mit Inputs: host, port, target_base_url, store_path. Buttons: Save Config, Reset Config, Test Target.

**Prompt C4 — Endpoint Table**

> Baue eine Tabelle "Endpoint Overview" mit Spalten: method, path, samples, versions, captures, last_changed. Mit Search, Method-Filter und Sortierung.

---

### 4.3 Endpoint Explorer

**Prompt E1 — Explorer Layout**

> Erzeuge ein 3-Spalten-Layout: links Filterbar, Mitte Endpoint-Liste, rechts Detailbereich mit Tabs.

**Prompt E2 — Detail Tabs**

> Detail-Tabs: Summary, Schema Versions, Captures, OpenAPI. Default: Summary.

---

### 4.4 Schema Drift

**Prompt D1 — Drift Timeline + Diff**

> Erzeuge oben eine Version-Timeline und darunter eine Diff-Tabelle. Diff zeigt Added Paths und Removed Paths getrennt. Ergänze Badges für Breaking Change Risiko.

---

### 4.5 Capture Inspector

**Prompt I1 — Split View**

> Erzeuge eine geteilte Ansicht: links Request Panel, rechts Response Panel. Beide mit Header, JSON-Viewer, Copy-Buttons.

**Prompt I2 — Redaction Notice**

> Ergänze oberhalb des JSON-Viewers einen Hinweis "Sensitive values are redacted" mit Zählern für redacted headers und redacted fields.

---

### 4.6 OpenAPI Export

**Prompt O1 — Preview + Actions**

> Baue OpenAPI Preview als JSON-Panel mit Buttons: Format JSON, Validate, Copy, Download JSON, Download YAML. Darunter Export History Tabelle.

---

### 4.7 Collections Export

**Prompt X1 — Liste + Detail**

> Baue links eine Collection-Liste (endpoint, samples, captures), rechts Collection-Detail mit Captures und Actions: Open, Copy, Download.

---

### 4.8 Settings

**Prompt S1 — Settings Sektionen**

> Erzeuge vier Sektionen: Environment Profiles, Redaction Rules Editor, Retention Limits, Replay Guardrails. Jede Sektion als Card mit Edit/View-State.

---

## 5) Komponenteninventar (kompakt)

### Navigation & Shell
- App Shell
- Sidebar Nav
- Topbar Status

### Control Panel
- Proxy Status Card
- Capture Config Form
- Quick Actions Bar
- Endpoint Overview Table

### Explorer & Drift
- Endpoint Filter Bar
- Endpoint List
- Endpoint Detail Tabs
- Version Timeline
- Drift Timeline
- Drift Diff Table
- Breaking Change Badges

### Inspector & Export
- Request Panel
- Response Panel
- JSON Viewer
- Redaction Notice
- OpenAPI Preview
- Export Actions
- Export History
- Collection List
- Collection Detail
- Export Download Controls

### Settings
- Environment Profiles
- Redaction Rules Editor
- Retention Limits
- Replay Guardrails

---

## 6) Zustände (global)

- loading
- empty
- error
- offline
- read_only

---

## 7) Stitch-Fehlertoleranz (wichtig)

Wenn Stitch Prompts ungenau umsetzt:

1. Prompt verkleinern (nur 1 Komponente)
2. Explizite Maße nennen (z. B. Sidebar 240px)
3. „Do not redesign“ ergänzen
4. Erst Struktur, dann Farben, dann States
5. Komponenten umbenennen statt neu generieren lassen

**Fallback-Formel:**

> Keep existing layout. Only modify component `<NAME>`. Do not change theme, spacing, or navigation.

---

## 8) Daten-Mapping (für spätere Bindung)

- `GET /_therapi/health` → Topbar Status, Proxy Status Card
- `GET /_therapi/summary` → Endpoint Overview Table, Endpoint List
- `GET /_therapi/drift` → Drift Timeline, Drift Diff Table
- `GET /_therapi/openapi.json` → OpenAPI Preview
- `GET /_therapi/collections.json` → Collection List, Collection Detail

---

## 9) Definition of Done für UI v0

- Alle 7 Seiten in Navigation erreichbar
- Jeder Screen hat Loading/Empty/Error-State
- Drift-Screen zeigt Added/Removed klar getrennt
- Inspector zeigt Redaction-Hinweis sichtbar
- OpenAPI Export-Aktionen im UI vorhanden
- Konsistente Tokens auf allen Screens

---

## 10) Übernahme aus `lootziffer666/design_system`

Ja — damit kann man **sehr gut arbeiten**. Für therAPI sind diese Leitlinien direkt nutzbar:

- **Start with feeling, not features** → zuerst Zielwirkung (ruhig, klar, kompetent), dann Komponenten.
- **Stabile Shell** → Navigation, Topbar und Container nicht pro Screen variieren.
- **Klare Hierarchie** → ein Fokus pro Seite, sekundäre Inhalte bewusst leiser.
- **Progressive Disclosure** → Details schrittweise offenlegen statt alles gleichzeitig zeigen.
- **Kindness without kitsch** → hilfreiche, ruhige Microcopy statt Alarmismus.

Diese Punkte passen vollständig zu einem Discovery-Tool mit hoher Informationsdichte.

---

## 11) Direkt anwendbare Zusatzregeln (für Stitch)

### 11.1 Was Stitch explizit **nicht** tun soll

> Do not redesign the app shell.
> Do not add KPI cards without clear user action.
> Do not increase visual noise (extra badges, gradients, decorative charts).
> Do not change navigation labels/order.

### 11.2 Qualitätsregeln pro Screen

- **Ein Screen, eine Hauptaussage** (primary panel klar sichtbar)
- **States Pflicht:** loading, empty, error, success, read_only
- **Fehler führen zur Lösung** (jede Fehlermeldung mit nächstem Schritt)
- **Sicherheitsstatus sichtbar** (Redaction, Export, destructive actions)

### 11.3 Tonalität (Microcopy)

- präzise
- ruhig
- respektvoll
- handlungsorientiert
- ohne Schuldzuweisung

---

## 12) Prompt-Block „Design Integrity Check“

Nach jeder Stitch-Iteration einmal ausführen:

> Evaluate this screen against five checks and return PASS/FAIL with one sentence each:
> 1) Stable shell preserved
> 2) Clear information hierarchy
> 3) Progressive disclosure applied
> 4) Low-noise visual density
> 5) Kind, actionable microcopy
> If any check fails, propose only minimal edits and do not redesign the full screen.

Damit werden die Guidelines aus `lootziffer666/design_system` operationalisiert, ohne den bisherigen therAPI-Aufbau zu brechen.
