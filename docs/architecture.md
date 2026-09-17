# System Architecture

## Layered Architecture

The system follows a layered architecture pattern where each layer has a clear responsibility and communicates only with adjacent layers.

```
┌─────────────────────────────────────────┐
│         USER / WEB BROWSER              │
├─────────────────────────────────────────┤
│     PRESENTATION LAYER                  │
│     HTML Templates + CSS + JavaScript   │
├─────────────────────────────────────────┤
│     API LAYER                           │
│     FastAPI Routes + Pydantic Schemas   │
├─────────────────────────────────────────┤
│     PROCESSING LAYER                    │
│     Video Processor (Orchestrator)      │
│     ├── Preprocessing Pipeline          │
│     ├── YOLO Detector                   │
│     ├── ByteTrack Tracker               │
│     └── Visualizer                      │
├─────────────────────────────────────────┤
│     BUSINESS LOGIC LAYER                │
│     ├── Violation Rule Engine           │
│     ├── Evidence Generator              │
│     └── Analytics Service               │
├─────────────────────────────────────────┤
│     DATA LAYER                          │
│     ├── SQLite Database                 │
│     ├── Repository (CRUD)               │
│     └── File System (evidence/output)   │
├─────────────────────────────────────────┤
│     INFRASTRUCTURE LAYER                │
│     ├── Configuration (Settings)        │
│     ├── Logging                         │
│     ├── Error Handling (Exceptions)     │
│     └── Validators                      │
└─────────────────────────────────────────┘
```

## Key Design Principles

1. **Separation of Concerns**: Each module handles one responsibility — detection, tracking, violations, storage, and presentation are independent.

2. **Dependency Direction**: Upper layers depend on lower layers, never the reverse. The database layer has no knowledge of the UI.

3. **Modularity**: The detector, tracker, and violation rules can be replaced independently without affecting other components.

4. **Configuration-Driven**: All thresholds, paths, and feature toggles are controlled via environment variables.

See [Architecture Diagram](diagrams/architecture.md) for the full Mermaid diagram.
