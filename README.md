# Projekt zum Modul Architecture-and-Integration und Seminar ISA

---
## 📚 Inhaltsverzeichnis
- [Sem ISA](#sem-isa)
- [Architecture-and-Integration](#architecture-and-integration)
- [Projektbeschreibung](#projektbeschreibung)
- [Architekturüberblick](#architekturüberblick)
  - [Komponenten](#komponenten)
  - [Routing Keys](#routing-keys)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
  - [1. RabbitMQ installieren](#1-rabbitmq-installieren)
  - [2. Python-Abhängigkeiten installieren](#2-python-abhängigkeiten-installieren)
- [Ausführung](#ausführung)
- [Anwendung](#anwendung)
- [Beispielausgabe (Konsolen)](#beispielausgabe-konsolen)


---
# Architecture-and-Integration
# 🧩 HIS Middleware Integration – Student Data Distribution

## 📘 Projektbeschreibung

In diesem Projekt wird eine Middleware-Lösung zur automatisierten Verteilung von Studierendendaten umgesetzt. Aktuell werden Daten manuell in drei Systeme eingetragen:

- **HIS**: Stammdatenpflege von Studierenden (Name, Matrikelnummer, Studienprogramme, Startdaten, Credits)
- **Peregos**: Anwendung des Prüfungsausschusses – benötigt Name, Matrikelnummer, Studienprogramme
- **WyseFlow**: Anmeldung zur Abschlussarbeit – benötigt vollständige Studierendendaten inkl. Credits

Ziel: **Automatisierte, fehlerfreie Weiterleitung** der HIS-Daten an beide Zielsysteme über eine Integrations-Middleware.

---

## ⚙️ Architekturüberblick

### Komponenten

- **Integration Middleware**: RabbitMQ (lokal installiert)
- **Anwendungen**:
  - `his.py`: GUI zur Dateneingabe und Nachrichtenversand
  - `peregos.py`: empfängt und verarbeitet relevante Daten für Peregos
  - `wyseflow.py`: empfängt vollständige Daten für WyseFlow

### Routing Keys

| Zielsystem  | Routing Key     | Empfängt folgende Daten                              |
|-------------|------------------|------------------------------------------------------|
| Peregos     | `peregos.info`   | Name, Matrikelnummer, Studienprogramme              |
| WyseFlow    | `wyseflow.info`  | Alle Daten inkl. Startdaten und Credits             |

---

## 🧰 Voraussetzungen

- Python 3.10+
- Lokale Installation von RabbitMQ (Standard-Ports: 5672)
- Python-Bibliotheken:
  - `pika` für RabbitMQ-Verbindung
  - `PyQt6` für GUI (nur `his.py`)

---

## 🧪 Installation

### 1. RabbitMQ installieren

**Windows:**
- Download von [https://www.rabbitmq.com/install-windows.html](https://www.rabbitmq.com/install-windows.html)
- Erlang ebenfalls installieren

---

### 2. Python-Abhängigkeiten installieren

```bash
pip install pika PyQt6
```

---

## ▶️ Ausführung

In **drei separaten Terminals** folgende Dateien starten:

```bash
# Terminal 1 – WyseFlow
python wyseflow.py

# Terminal 2 – Peregos
python peregos.py

# Terminal 3 – HIS GUI
python his.py
```

---

## 👨‍🎓 Anwendung

In der HIS-GUI:

1. Name, Matrikelnummer, Studienprogramme (kommagetrennt), Startdaten und Credits eingeben
2. Auf **„+ Hinzufügen“** klicken – Validierung erfolgt automatisch
3. Auf **„✔ Alle senden“** klicken – Daten werden über RabbitMQ versendet
4. In den Konsolen von `peregos.py` und `wyseflow.py` erscheinen die empfangenen Nachrichten

---

## ✅ Beispielausgabe (Konsolen)

**Peregos:**
```
[Peregos] Received: {"name": "Anna Müller", "Martikelnummer": 123456, "programs": ["WI", "AI"]}
```

**WyseFlow:**
```
[WyseFlow] Received: {"name": "Anna Müller", "Martikelnummer": 123456, "programs": [...], "startDates": {...}, "creditsPerProgram": {...}, "totalCredits": 180}
```
---

# Sem ISA
# CO₂ Emission Analysis

> Automatisierte Extraktion und Visualisierung von CO₂-Daten aus PDFs mit RPA (UiPath) und OCR.  
> Projektkontext: Seminar *Information Systems Architecture* 

---

## Inhaltsverzeichnis
- [Kurzbeschreibung](#kurzbeschreibung)
- [Architektur & Workflow](#architektur--workflow)
- [Tech-Stack](#tech-stack)
- [Setup (lokal)](#setup-lokal)
- [Nutzung](#nutzung)
- [Ergebnisse](#ergebnisse)
- [Herausforderungen & Learnings](#herausforderungen--learnings)

---

## Kurzbeschreibung
Prototyp zur Extraktion CO₂-relevanter Daten aus PDF-Berichten, strukturierter Export nach Excel und automatisierte Erstellung von Diagrammen (Pivot + Charts), die in eine PowerPoint-Präsentation überführt werden. Ziel ist eine schnellere, konsistente und reproduzierbare Auswertung von Emissionen für Berichte und Entscheidungen.

## Architektur & Workflow
1. **PDF importieren**: Emissionsdaten (tabellarisch/halbstrukturiert).  
2. **OCR**: Strukturierte Extraktion relevanter Felder (Material, Einheit, Emissionsfaktor, Unsicherheit, Quelle) in ChatGPT.  
3. **Excel-Aufbereitung**: Validierung & Normalisierung als Input für Pivot/Charts.  
4. **Diagrammerstellung**: Balken-/Tortendiagramme je Kategorie/Material.  
5. **Export nach PowerPoint**: Pro Diagramm eine Folie (Dashboard-Layout).  

## Tech-Stack
- **RPA**: UiPath (Studio/Community/Academic)
- **OCR**: ChatGPT Plus
- **Office-Outputs**: Excel (Pivot, Charts), PowerPoint (Slides)
- **Sonstiges**: BPMN/Camunda zur Prozessdokumentation (Happy/Unhappy Path)

## Setup (lokal)
- **Voraussetzungen**:  
  - UiPath Studio installiert  
  - Microsoft Excel & PowerPoint verfügbar  
  - Beispiel-PDFs mit Emissionsdaten
- **Konfiguration**:  
  - Projekt öffnen  
  - Ein-/Ausgabepfade im UiPath-Workflow anpassen  
  - (Optional) OCR-/LLM-Konfiguration und Prompt-Vorlagen parametrieren

## Nutzung
1. UiPath-Workflow starten.  
2. PDF auswählen → **Extraktion** ausführen.  
3. **Excel** wird erzeugt/aktualisiert (strukturierte Daten + Pivots).  
4. **Charts** generieren und automatisch in **PowerPoint** einfügen.  
5. PPT prüfen

## Ergebnisse
- Übersichtliche Ranglisten der emissionsintensivsten Materialien/Kategorien.  
- Standardisierte Folien (ein Chart pro Folie) für Reporting/Reviews.  
- Nachvollziehbarer End-to-End-Prozess (BPMN) inklusive Fehlerpfaden.

## Herausforderungen & Learnings
- Sehr große/uneinheitliche Tabellen → OCR-Fehler / Spaltenverschiebungen möglich.  
- Besserer Durchsatz bei **„ein Datensatz → ein Pivot/Chart → ein Slide“** als bei Sammelverarbeitung.  
- Datenqualität (Einheiten, Dezimaltrennzeichen) beeinflusst die Diagrammvalidität 

---

