---
team: Echoes.ai
session: 04
date: 2026-09-22
members:
  - name: Pratham Bharati
    github: prathambharati
    hat: Product
  - name: Saurabh
    github: saurabh1712
    hat: Engineering
  - name: Surabhi More
    github: SurabhiMore
    hat: Data&Eval
  - name: Kshiti Deshpande
    github: kshitideshpande
    hat: Users&Research
  - name: Aditi Karanjkar
    github: aditikaranjkar
    hat: Operations
north_star:
  metric: Grounded Answer Accuracy
  value: TBD (Session 5 Baseline)
  previous: N/A
---

## Shipped this week
- **Lean Canvas v2 & Product Roadmap v3** in [`artifacts/lean_canvas.md`](../artifacts/lean_canvas.md) and [`artifacts/roadmap.md`](../artifacts/roadmap.md) (evidence: Issue #3, PR #4).
- **Voice Pipeline System Architecture & Git Setup** in [`artifacts/architecture.md`](../artifacts/architecture.md) and `.gitignore` (evidence: Issue #1, PR #2).
- **Team Process ("How we work")** in [`artifacts/team_process.md`](../artifacts/team_process.md) (evidence: Issue #6).
- **User Research Plan & Evidence Folder Setup** (evidence: Issue #5).
- **Repository Setup & Branch Protection**: Configured `main` branch protection requiring 1 approving review per PR.

## User evidence
- Session 4 represents our initial setup and architecture phase. Kshiti (Users & Research) created the user research plan and structured the `evidence/` directory for raw artifact collection.
- Recruiting protocol established for 3 non-team users for the Session 5 interactive voice prototype test.
- **Raw artifact**: User testing protocol and consent structure stored in `artifacts/` for Session 5 execution.

## Metrics snapshot
- **Grounded Answer Accuracy**: Target baseline to be established in Session 5.
- **Recall@5 (BM25 Keyword Search)**: Evaluation dataset being curated by Surabhi for Session 5 execution.
- **Target Voice Latency**: < 2.0 seconds end-to-end (Whisper STT -> RAG LLM -> TTS).
- Measured on: Held-out synthetic and real visitor question dataset (Session 5).
- Is this the same model that is running in the product? Yes (van Gogh pilot persona RAG pipeline).

## What did not work
- **Dataset Limitation**: Our initial assumption was that The Met's CC0 dataset would provide rich descriptive text for exhibits. Upon inspection, we discovered it only contains catalog metadata (title, date, medium) without explanatory narratives.
- **Adaptation & Pivot**: We pivoted to a persona-based approach, combining Vincent van Gogh's personal letters (public domain) and Wikipedia articles (CC BY-SA 4.0) as grounded source texts. This allows rich conversational Q&A while maintaining strict attribution.

## Challenges / blockers
- **Compute & Latency Constraints**: Running Whisper transcription, vector/keyword retrieval, LLM response generation, and TTS synthesis sequentially within a 2-second budget on free hosting tiers (Hugging Face Spaces).
- **Mitigation Strategy**: Engineering will benchmark each component independently in Session 5 to identify bottlenecks.

## Next week's goal
- Ship the first working voice loop MVP (Speech-to-Text -> RAG Search -> Text-to-Speech) and report our first BM25 Recall@5 baseline metric.

## Individual contributions
- **Pratham Bharati (Product)**: Authored Lean Canvas v2 and Product Roadmap v3 detailing session-by-session build deliverables for all team members (evidence: PR #4, Issue #3).
- **Saurabh (Engineering)**: Designed the voice pipeline system architecture, component interaction flow, and initial `.gitignore` (evidence: PR #2, Issue #1).
- **Surabhi More (Data & Eval)**: Audited licensing and structured source text collection (van Gogh letters & Wikipedia) for the corpus.
- **Kshiti Deshpande (Users & Research)**: Established user research methodology and testing protocol for Session 5 trial (evidence: Issue #5).
- **Aditi Karanjkar (Operations)**: Verified repository branch protection compliance, configured project board and milestones, authored [`artifacts/team_process.md`](../artifacts/team_process.md), and compiled `reports/session04.md` (evidence: Issue #6).

## Lean canvas changes (if any)
- **Version 2 Updates (Sept 22)**: Shifted system design from hardcoded artwork guides to a persona-agnostic RAG pipeline. Selected Vincent van Gogh as the pilot persona due to open-access letters and museum collections. Added explicit risk tracking for source text depth.