# 🔄 BidEngine Complete System Workflows & Lifecycle Specification

This document details the end-to-end operational workflows, data transformations, and inter-process communication sequences across the 5 distinct lifecycle stages of the **BidEngine** proposal automation platform.

---

## 1. End-to-End Proposal Lifecycle Workflow

```mermaid
stateDiagram-v2
    [*] --> Upload: Ingest RFP (.pdf/.docx)
    Upload --> Extraction: Stage 1 - Parse & NER Analysis
    
    state Extraction {
        [*] --> TextParsing: Extract Raw Text & Tables
        TextParsing --> EntityRecognition: NER Engine (Deadlines, Budget, Specs)
        EntityRecognition --> MetadataJSON: Store in Workspace DB
    }
    
    Extraction --> Compliance: Stage 2 - Compliance Audit
    
    state Compliance {
        [*] --> LoadRules: Ingest Mandatory Clauses
        LoadRules --> EvaluateRisk: Cross-reference Corporate Guidelines
        EvaluateRisk --> RiskMatrix: Generate Pass/Warning/Fail Report
    }
    
    Compliance --> CapabilityMatch: Stage 3 - Capability Alignment
    
    state CapabilityMatch {
        [*] --> EmbedRequirements: Generate Vector Embeddings
        EmbedRequirements --> VectorSearch: Query Capability Library
        VectorSearch --> ReferenceRank: Rank Top Case Studies & Tooling
    }
    
    CapabilityMatch --> AIDrafting: Stage 4 - Multi-Agent Proposal Generation
    
    state AIDrafting {
        [*] --> ArchitectAgent: Solution & Architecture Outlining
        ArchitectAgent --> WriterAgent: RAG-Informed Narrative Drafting
        WriterAgent --> AuditorAgent: Compliance & Page Limit Verification
    }
    
    AIDrafting --> WinScoring: Stage 5 - ML Win Probability Prediction
    
    state WinScoring {
        [*] --> AggregateFeatures: Combine Match, Price & Compliance Metrics
        AggregateFeatures --> ScikitInference: Run Regression Model (win_scorer.pkl)
        ScikitInference --> RecommendationEngine: Output Probability & Optimization Advice
    }
    
    WinScoring --> Export: Export Final Proposal (.docx/.pdf)
    Export --> [*]
```

---

## 2. Stage-by-Stage Detailed Workflows & Sequence Diagrams

### Stage 1: RFP Ingestion & NER Extraction Workflow
When a proposal manager initiates a new workspace, the raw tender document must be converted into actionable machine-readable data.

```mermaid
sequenceDiagram
    autonumber
    actor PM as Proposal Manager
    participant FE as Next.js Workspace (/extract)
    participant API as FastAPI Upload Router
    participant PARSER as Document Parser Service
    participant NER as NER Extractor (ner_extractor.py)
    participant DB as MongoDB Workspace Store

    PM->>FE: Upload RFP Document (PDF/DOCX)
    FE->>API: POST /api/upload (Multipart Form Data)
    API->>PARSER: Ingest binary file & convert to structured text
    PARSER->>NER: Execute Natural Language Processing & NER
    NER->>NER: Identify: Deadlines, Budget Caps, ISO Specs, Evaluation Weights
    NER-->>API: Return Structured Extraction JSON
    API->>DB: Save Workspace Extraction State
    API-->>FE: Return Extracted Entities & Summary
    FE->>PM: Render Interactive Extraction Dashboard
```

---

### Stage 2: RFP Compliance Audit Workflow
Before investing engineering hours, BidEngine verifies that the organization meets mandatory RFP criteria.

```mermaid
sequenceDiagram
    autonumber
    actor PM as Proposal Manager
    participant FE as Next.js Workspace (/compliance)
    participant API as Compliance Router
    participant COMP as Compliance Engine (compliance_engine.py)
    participant DB as MongoDB Workspace Store

    PM->>FE: Initiate Compliance Audit
    FE->>API: POST /api/compliance/check (Workspace ID)
    API->>DB: Fetch Extracted Mandatory Clauses & Specs
    API->>COMP: Run Rule-Driven Clause Evaluation
    COMP->>COMP: Check Financial Caps, ISO 27001/SOC2, Legal Terms
    COMP-->>API: Generate Risk Assessment Matrix (Pass/Warning/Fail)
    API->>DB: Persist Compliance Matrix
    API-->>FE: Return Risk Flags & Clarification Suggestions
    FE->>PM: Display Color-Coded Compliance Report Card
```

---

### Stage 3: Hybrid RAG & Capability Matching Workflow
To generate realistic proposals, BidEngine aligns specific RFP requirements with verified corporate past performance.

```mermaid
sequenceDiagram
    autonumber
    actor PM as Proposal Manager
    participant FE as Next.js Workspace (/match)
    participant API as Match Router
    participant RAG as Hybrid RAG Engine (hybrid_rag_engine.py)
    participant VEC as Vector Embeddings Index
    participant LIB as Capability Library (capability_library.json)

    PM->>FE: Trigger Capability Search
    FE->>API: POST /api/match (Technical Requirements List)
    API->>RAG: Execute Semantic & Keyword Retrieval
    par Dense Vector Search
        RAG->>VEC: Cosine Similarity Search (Embeddings)
    and Sparse Keyword Search
        RAG->>LIB: BM25 / Exact Keyword Query (Tooling, Technologies)
    end
    RAG->>RAG: Reciprocal Rank Fusion & Deduplication
    RAG-->>API: Return Top-Rated Case Studies, Team Resumes & Architectures
    API-->>FE: Stream Capability Alignment Matrix
    FE->>PM: Present Matched Capabilities for Approval
```

---

### Stage 4: CrewAI Autonomous Proposal Drafting Workflow
The proposal drafting pipeline utilizes a collaborative multi-agent architecture where agents challenge and refine each other's output.

```mermaid
sequenceDiagram
    autonumber
    actor PM as Proposal Manager
    participant FE as Next.js Workspace (/draft)
    participant API as Draft Router
    participant CREW as CrewAI Pipeline (crewai_pipeline.py)
    participant RAG as Hybrid RAG Context Provider
    participant LLM as OpenAI / LLM Inference Engine

    PM->>FE: Generate AI Proposal Draft
    FE->>API: POST /api/draft/generate (Workspace ID, Approved References)
    API->>CREW: Initialize Multi-Agent Drafting Crew
    
    Note over CREW,LLM: Step 1: Lead Architect Agent Outlines Solution
    CREW->>RAG: Request Technical Context & Reference Architectures
    CREW->>LLM: Generate Technical Approach & System Diagram
    
    Note over CREW,LLM: Step 2: Proposal Writer Agent Drafts Narratives
    CREW->>LLM: Synthesize Executive Summary, Management Plan & Pricing Narrative
    
    Note over CREW,LLM: Step 3: Compliance Auditor Agent Verifies Quality
    CREW->>LLM: Audit generated narrative against Stage 2 Compliance Matrix
    
    CREW-->>API: Return Consolidated Proposal Document Sections
    API-->>FE: Stream Formatted Markdown & Sections
    FE->>PM: Render Editable Rich-Text Proposal Editor
```

---

### Stage 5: Machine Learning Win Prediction Workflow
Before final submission, BidEngine evaluates proposal competitiveness using statistical regression.

```mermaid
sequenceDiagram
    autonumber
    actor PM as Proposal Manager
    participant FE as Next.js Workspace (/score)
    participant API as Score Router
    participant SCORER as ML Scorer Service (ml_win_scorer.py)
    participant MODEL as Serialized Scikit-Learn Model (win_scorer.pkl)
    participant HIST as Historical Bids Store (bid_history.json)

    PM->>FE: Request Win Probability Analysis
    FE->>API: POST /api/score/predict (Proposal Features & Metrics)
    API->>SCORER: Assemble Feature Vector (Alignment, Price Delta, Compliance)
    SCORER->>HIST: Query Historical Win/Loss Benchmarks
    SCORER->>MODEL: Execute Model Inference (.predict / .predict_proba)
    MODEL-->>SCORER: Return Raw Probability Score & Feature Importances
    SCORER->>SCORER: Generate Actionable Optimization Advice (e.g., "Lower margin by 3%")
    SCORER-->>API: Return Score Percentage & Recommendations
    API-->>FE: Return Win Probability Gauge & Strategic Feedback
    FE->>PM: Display Win Rate Dashboard & Final Export Options
```

---

## 3. Data Transformation & State Evolution

As a proposal moves through the BidEngine workspace pipeline, the underlying data structure evolves from raw unstructured documents to a fully scored, structured proposal artifact.

```text
[Raw RFP Upload: .pdf / .docx]
        |
        v  (NER Extractor)
[Structured Extraction State: { deadlines: [...], budget: "...", clauses: [...] }]
        |
        v  (Compliance Engine)
[Compliance Risk Matrix: { pass: 14, warnings: 2, fails: 0, matrix: [...] }]
        |
        v  (Hybrid RAG Engine)
[Matched References Context: { case_studies: [...], resumes: [...], tech_stack: [...] }]
        |
        v  (CrewAI Multi-Agent Pipeline)
[Draft Proposal Document: { executive_summary: "...", technical_approach: "...", pricing: "..." }]
        |
        v  (ML Win Scorer)
[Final Workspace Artifact: { win_probability: 84.5%, recommendations: [...], export_ready: true }]
```
