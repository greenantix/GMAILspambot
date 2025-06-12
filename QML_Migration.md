**Modern QML UI Migration Plan for Claude Code: Gmail Spam Bot Organizer**

---

### 🌟 Overview

Refactor the existing mixed React/PyQt frontend into a modern, clean **QML (Qt Quick)** interface, while preserving all back-end logic and functionality across:

* Real-time processing (LM Studio)
* Batch Gemini analysis
* Gmail API rule application
* Backlog cleaning
* Audit log viewing & restoring
* Settings configuration

This plan replaces the current PyQt UI with **QML + PySide6**, allowing declarative UI components, modern visuals, and tight Python integration via `QtQuick` signals and slots.

---

### 🛠️ Phase 1: Core QML Application Shell

#### Files to Create

* `main.qml`
* `Dashboard.qml`
* `BacklogView.qml`
* `AuditLog.qml`
* `SettingsView.qml`
* `components/SidebarItem.qml`
* `AppWindow.qml` (optional wrapper)

#### Shell Layout

* Use `ApplicationWindow` (QtQuick.Controls)
* Left sidebar with:

  * Icon + label menu items
  * Connected to `StackView` for main view switching

#### Components

```qml
ListView {
  model: ["Dashboard", "Backlog", "Audit", "Settings"]
  delegate: SidebarItem {
    label: modelData
    icon: appropriateIcon(modelData)
    onClicked: stackView.currentIndex = index
  }
}
```

---

### 🔄 Phase 2: QML <-> Python Integration

Use `PySide6.QtQml` and `QQmlApplicationEngine`.
Expose backend Python objects to QML context:

```python
engine.rootContext().setContextProperty("gmailCleaner", GmailLMCleaner())
engine.rootContext().setContextProperty("auditManager", AuditManager())
engine.load("qml/main.qml")
```

Use `@Slot()` decorators in backend for QML-triggered functions.

---

### 🔹 Phase 3: Feature Mapping by View

#### 📊 Dashboard.qml

* Display live stats from:

  * `check_status.py`
  * Gmail unread count
  * Last processed email
  * LLM health
* Buttons to start:

  * Real-time run
  * Batch Gemini run
  * Export email list

#### 🔎 BacklogView\.qml

* Start `bulk_processor.py` with custom batch size
* Show running logs in text area (`TextArea` or `LogView.qml`)
* Optional: progress bar using signals

#### ♻️ AuditLog.qml

* Load parsed audit logs
* Filter by date, label, action
* Table view of audit entries
* Buttons:

  * Restore selected
  * Export CSV

#### ⚙️ SettingsView\.qml

* Load and save `settings.json`
* Editable fields:

  * Retention days
  * API endpoints
  * Paths (logs, exports)
* Realtime validation and save button

---

### 🔢 Phase 4: Logic Refactor to Python Services

* Move any PyQt slots/signals into service classes
* Example:

  * `AuditManager`: parse logs, apply restore
  * `SettingsManager`: JSON IO for config
  * `EmailRunner`: handles real-time run + batch

---

### 📷 Phase 5: Icon & Style

* Use Lucide or Material SVG icons
* Store in `qml/assets/icons/`
* Style with `Material.Dark` theme:

```qml
Material.theme: Material.Dark
Material.accent: Material.Teal
```

---

### 📆 Phase 6: Launch Wrapper

Python entrypoint (`main.py`):

```python
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine

app = QApplication([])
engine = QQmlApplicationEngine()
engine.load("qml/main.qml")
app.exec()
```

Wrap with `start_stable.sh` and optionally expose via Tauri if cross-platform packaging is needed.

---

### 📅 Deliverables Checklist for Claude Code

* [ ] All logic in Py files retained
* [ ] Each QML view created and wired
* [ ] Sidebar + icons + routing working
* [ ] Full audit log viewer & restore from GUI
* [ ] Real-time run + LLM batch trigger buttons
* [ ] Settings UI with live config save
* [ ] Works as standalone desktop app

---

### 📱 Optional Future Upgrade

* Add `SystemMonitor.qml` to show CPU/memory/net
* Run `tail -f` on logs into `LiveLogView.qml`
* Support filter import/export GUI

---

Claude should **avoid breaking Python logic** and instead expose functions via `@Slot()` decorators and integrate into QML views.
Do not convert logic to JavaScript. Keep all decision/processing Python-native.
