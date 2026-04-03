## Was im gemergten Stand bereits vorhanden ist

Im aktuellen Repo steckt jetzt ein echter Python-MVP unter `src/therapi` mit genau diesen Kernbausteinen:

* `proxy.py`
* `schema.py`
* `registry.py`
* `openapi.py`
* plus Tests in `tests/test_schema_and_openapi.py`

Außerdem sagt die `README.md` exakt dasselbe Zielbild:

1. HTTP Capture
2. probabilistische JSON-Schema-Inferenz
3. versionierte Schema Registry
4. OpenAPI Export

---

# Was therapi schon kann

## Bereits vorhanden

### 1. **HTTP Capture / Proxy**

Der Proxy leitet Requests weiter, zeichnet Request/Response auf und aggregiert pro Endpoint (`METHOD + path`).

### 2. **JSON-Erkennung**

`parse_json_if_possible()` versucht Bodies als JSON zu parsen. Nicht-JSON wird aktuell ignoriert.

### 3. **Probabilistische Schema-Inferenz**

`SchemaNode` erkennt:

* Typen
* Objektfelder
* Feldpräsenz
* Arrays
* optionale vs. häufig vorhandene Felder

### 4. **Versionierung per Struktur-Fingerprint**

Wenn sich die **Struktur** eines Endpoints ändert, wird eine neue Version erzeugt.

### 5. **OpenAPI-Export**

Aus den beobachteten Snapshots wird dynamisch eine OpenAPI 3.0.3 Spec gebaut.

### 6. **Interne Diagnose-Endpunkte**

* `/_therapi/health`
* `/_therapi/summary`
* `/_therapi/openapi.json`

### 7. **Persistenz**

Schon da, aber minimal.

Die Registry wird als JSON gespeichert und beim Start geladen.

---

# Funktionen aus anderen Tools, die für therapi jetzt noch wirklich nützlich wären

## P1 — klar sinnvoll

### 1. **Request/Response Override**

**Vorbild:** Requestly

Therapi kann aktuell **beobachten**, aber nicht aktiv **überschreiben**.

Das wäre nützlich für:

* API-Verhalten simulieren
* Fehlerfälle erzwingen
* Frontends gegen manipulierte Antworten testen

**Behalten:** ja
**Bloat:** nein

---

### 2. **Mocking aus Capture**

**Vorbild:** Requestly

Du hast Capture + Schema + OpenAPI schon.
Der logische nächste Schritt ist:

> beobachteten Endpoint direkt als Mock ausspielen

Das wäre ein echter Volltreffer.

**Behalten:** ja
**Bloat:** nein

---

### 3. **Dateibasierte Collections / Replay-Artefakte**

**Vorbild:** Bruno

Du exportierst aktuell OpenAPI, aber noch keine brauchbaren Request-Sammlungen.

Sinnvoll wären:

* gespeicherte Beispielrequests
* replaybare Collections
* diff-freundliche Textdateien

---

### 4. **Environment-Variablen**

**Vorbild:** Bruno / Hoppscotch

Gerade für Replay und Export sinnvoll:

* Base URL austauschbar
* Auth separat
* dev/stage/prod konfigurierbar

---

### 5. **Secret Redaction / sichere Speicherung**

**Vorbild:** API-Security-Ökosystem allgemein

Aktuell werden Header einfach durchgereicht, aber es gibt noch keine erkennbare Schutzschicht für:

* Authorization
* Cookies
* API Keys
* sensible Felder im Body

Das ist kein Luxus, das ist Pflicht.

---

### 6. **Replay-Throttling / Rate-Limit-Bewusstsein**

**Vorbild:** Kong / APISIX

Therapi kann schnell in die Falle laufen, APIs zu hart zu befeuern.

Sinnvoll:

* Retry-Backoff
* Rate-Limit-Erkennung
* Replay-Drosselung

---

## P2 — sinnvoll, aber erst nach P1

### 7. **Pre-/Post-Request Hooks**

**Vorbild:** Hoppscotch / Requestly

Kleine Skript-Hooks wären nützlich für:

* Token erneuern
* Parameter einsetzen
* Antwort prüfen

Aber bitte klein halten. Keine Skriptorgie.

---

### 8. **Transformation Pipeline**

**Vorbild:** Tyk / APISIX

Wenn therapi später Daten normieren soll, ist eine kleine Pipeline stark:

* Felder umbenennen
* Responses normalisieren
* provider-spezifische Formate angleichen

**Bloat-Risiko:** mittel, wenn zu generisch gebaut

---

### 9. **Bessere Summary / Drift-Ansicht**

**Vorbild:** leichte Observability-Ideen

Du hast schon `/_therapi/summary`, aber noch keine echte Sicht auf:

* was sich geändert hat
* wann sich Struktur änderte
* welche Felder neu sind
* welche optional geworden sind

Das wäre sehr wertvoll.

---

# Was du dir ausdrücklich sparen kannst

Für therapi aktuell ziemlich sicher unnötig:

* Developer Portal
* Monetarisierung
* Team-/Tenant-Management
* Kubernetes-/Ingress-Zeug als Produktkern
* große Dashboards
* Collaboration-Cloud
* vollständiges API-Gateway-Nachbauen

Das wäre alles Ballast.

---

# Harte, bereinigte Funktionsmatrix

## Schon vorhanden

* HTTP Capture
* JSON Parsing
* probabilistische Schema-Inferenz
* Struktur-Fingerprints
* Schema-Versionierung
* OpenAPI-Export
* Registry-Persistenz
* Basis-Tests
* interne Diagnose-Endpunkte

## Fast naheliegend als nächster Schritt

* Mocking aus Capture
* Request/Response Override
* Replay-Artefakte / Collections
* Secret Redaction
* Environment-Variablen
* Drift-/Change-Ansicht
* Rate-Limit-/Retry-Bewusstsein

## Später, falls überhaupt

* kleine Hook-Skripte
* leichte Transform-Pipeline
* breitere Protokolle

## Weglassen

* Enterprise-Management-Kram
* schwere Gateway-Funktionen
* Org-/Billing-/Portal-Zeug

---

> **welche kleinen, präzisen Fähigkeiten fehlen dem bestehenden Kern noch?**

Und da wäre meine nüchterne Reihenfolge:

1. **Secret Redaction**
2. **Mocking aus Capture**
3. **Replay/Collections**
4. **Environment Support**
5. **Change/Drift View**
6. **Rate-Limit-Schutz**
7. **erst danach Hooks/Transformation/UI

