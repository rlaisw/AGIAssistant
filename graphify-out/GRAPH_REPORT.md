# Graph Report - AgenticRAG  (2026-10-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1863 nodes · 3587 edges · 125 communities (93 shown, 32 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 508 edges (avg confidence: 0.92)
- Token cost: 10,994 input · 8,879 output

## Graph Freshness
- Built from commit: `ba9f4624`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Prerequisite Check CLI
- SSRF Guarded Fetch
- RL Agent Shared Code
- Dual-System Workflow Contracts
- Reflexion Graph Agent
- OneDrive Freshness Probe
- System 1 Decision Node
- Logging Setup Configuration
- Vector Store Wrapper
- Agentic RAG MCP Server
- Migration Error Handling
- Spec-Kit Shell Helpers
- Specialty Web Search
- OneDrive Contract Tests
- OneDrive Test Fakes
- Logging Design Decisions
- Logging and Tool Models
- State Store Methods
- OneDrive On-Demand Tests
- Episodic Memory Records
- Web Search Providers
- OneDrive On-Demand Spec
- OneDrive Source Connector
- Logging Integration Tests
- One-Time Migration Tests
- Server Transport Config
- OneDrive Graph Auth
- Answer Synthesis
- Rule-Based Evaluator
- Specialty Search Integration
- Specialty Search Checklist
- Fallback Provenance Tests
- Web Research Integration
- Laya Runtime
- Dify Sidecar Server
- Spec-Kit PowerShell Helpers
- Web Research Design
- Graph Connector Tests
- OneDrive Ingestion Tasks
- Specialty Search Contract
- Agentic RAG Architecture
- Speckit Commands
- Speckit Workflows
- MCP Server Core
- Web Research Contract
- Reflexion Quickstart Tests
- Decision Routing Tests
- OneDrive Ingestion Spec
- Port Alignment Spec
- MCP Contract Tests
- State Snapshot Tests
- Logging Contract Tests
- End-to-End Tests
- OneDrive On-Demand Tools
- Success Criteria Tests
- Implementation Task Plan
- AgenticRAG Constitution
- Test Fixture Corpus
- Ask Response Contract
- Port Alignment Tasks
- OneDrive Ingestion Data Model
- CocoIndex Code Settings
- SQLite State Tools
- Deploy Script
- Question Session Entities
- FastMCP Stdio Server
- Optional Graph Search Layer
- Web Search Fallback
- Multi-Engine Search Testing
- D7: Rendering — stdlib string templates, no engine
- OneDrive Auth Spec
- Spec-kit feature specification template
- Agentic RAG MCP
- Reflexion LangGraph Flow
- Web Search Scrape Tasks
- OneDrive Staleness Research
- Port Alignment Quickstart
- Local Folder Q&A
- Incremental Update
- Multi-source Deep Research
- MCP Client Wiring
- OneDrive Auth Contract
- Edge Case Tests
- RL Agent Inference
- Web Research Implementation
- Specialty Search Plan
- Specialty Search Quickstart
- Specialty Search Tasks
- Provider Chain Tests
- Logging Task Plan
- Research Extraction Tests
- OneDrive Ingestion Plan
- HTTP Test Server
- RL Data Encoding
- OneDrive Ingestion Research
- Logging Status Contract
- Logging Implementation Plan
- Logging Feature Spec
- Question Planner
- RL Agent Confidence
- SSRF Web Research
- Logging Checklist
- Research Page Renderer
- Local Embeddings
- Domain Filtering
- Dify Specialty Agent
- Decision Model Encoder
- Logging Quickstart
- Logging User Stories
- Task Dependencies
- TD Lambda Targets
- Reflexion End-State Tests
- Feature Documentation
- Site-Scoped Query Builder
- AGENTS.md

## God Nodes (most connected - your core abstractions)
1. `build_server()` - 80 edges
2. `ProviderError` - 41 edges
3. `StateStore` - 40 edges
4. `SourceAuthError` - 33 edges
5. `Config` - 33 edges
6. `sources_auth()` - 30 edges
7. `ask()` - 25 edges
8. `status()` - 23 edges
9. `OneDriveSource` - 21 edges
10. `resolve_template_content()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Notes` --references--> `GraphAuth`  [INFERRED]
  specs/006-onedrive-ingestion/checklists/requirements.md → src/agentic_rag_mcp/sources/graph_auth.py
- `EmbedOutcome (onedrive_embed_files per-file results)` --references--> `status()`  [INFERRED]
  specs/007-onedrive-on-demand/data-model.md → src/agentic_rag_mcp/server.py
- `Constitution Check` --references--> `status()`  [INFERRED]
  specs/008-app-logging/plan.md → src/agentic_rag_mcp/server.py
- `Summary` --references--> `status()`  [INFERRED]
  specs/008-app-logging/plan.md → src/agentic_rag_mcp/server.py
- `2. Live check (running sidecar)` --references--> `status()`  [INFERRED]
  specs/008-app-logging/quickstart.md → src/agentic_rag_mcp/server.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Dual-System Request Flow: System 1 decision → FR-005 route mapping → execution path → ask response contract** — specs_002_laya_reflexion_nodes_spec_system_1_decision_node, specs_002_laya_reflexion_nodes_spec_fr005_route_mapping, specs_002_laya_reflexion_nodes_spec_system_2_reflexion_graph, specs_002_laya_reflexion_nodes_contracts_ask_response_ask_tool_contract [EXTRACTED 1.00]
- **Supersedes Replacement Scope: OLD components → NEW dual-system design** — specs_002_laya_reflexion_nodes_spec_single_label_classifier, specs_002_laya_reflexion_nodes_spec_keyword_heuristic_fallback, specs_002_laya_reflexion_nodes_spec_monolithic_deliberation_loop, specs_002_laya_reflexion_nodes_spec_hit_count_sufficiency_gate, specs_002_laya_reflexion_nodes_spec_system_1_decision_node, specs_002_laya_reflexion_nodes_spec_system_2_reflexion_graph, specs_002_laya_reflexion_nodes_spec_evaluator_stage [EXTRACTED 1.00]
- **System 2 Reflexion Loop: Actor → Evaluator → Self-Reflector → Episodic Memory** — specs_002_laya_reflexion_nodes_spec_actor_stage, specs_002_laya_reflexion_nodes_spec_evaluator_stage, specs_002_laya_reflexion_nodes_spec_self_reflector_stage, specs_002_laya_reflexion_nodes_data_model_episodicmemory, specs_002_laya_reflexion_nodes_spec_system_2_reflexion_graph [EXTRACTED 1.00]
- **Incremental ingestion pipeline (CocoIndex change detection into LanceDB chunks with dedup by content hash)** — specs_001_agentic_rag_mcp_plan_cocoindex_pipeline, specs_001_agentic_rag_mcp_plan_lancedb_vector_store, specs_001_agentic_rag_mcp_data_model_document, specs_001_agentic_rag_mcp_data_model_chunk, specs_001_agentic_rag_mcp_data_model_source [INFERRED 0.95]
- **System 1/System 2 question routing (Laya decision layer steering between fast retrieval and the LangGraph deliberative loop)** — specs_001_agentic_rag_mcp_research_d5_laya_routing, specs_001_agentic_rag_mcp_plan_langgraph_deliberative_loop [INFERRED 0.95]

## Communities (125 total, 32 thin omitted)

### Community 0 - "Prerequisite Check CLI"
Cohesion: 0.06
Nodes (60): Args, _available_docs(), _check_dir(), _check_file(), _dir_has_entries(), _json_line(), main(), _parse_args() (+52 more)

### Community 1 - "SSRF Guarded Fetch"
Cohesion: 0.16
Nodes (10): guarded_get(), ScrapeBlocked, _Resp, test_private_destinations_refused(), test_public_ip_allowed_and_returned(), fake_get(), test_redirect_chain_capped(), fake_get() (+2 more)

### Community 2 - "RL Agent Shared Code"
Cohesion: 0.13
Nodes (6): aurc(), auroc(), ece_score(), make_token_batches(), pack_groups(), spearman()

### Community 3 - "Dual-System Workflow Contracts"
Cohesion: 0.07
Nodes (41): Specification Quality Checklist: Dual-System Workflow, ask MCP Tool Response Contract (preserved fields + decision/reflections extensions), Pre-existing Contract Test Suite (tests/contract/), Dify Chatflow (client consumer of the ask tool), Contract: ask Tool Response, decide(question) → DecisionResult (System 1 decision node operation), Decision Primitives: choice, score, noul (one-pass three-question batch), Contract: System 1 Decision Schema (+33 more)

### Community 4 - "Reflexion Graph Agent"
Cohesion: 0.14
Nodes (8): ReflexionAgent, test_budget_exhaustion_low_confidence_and_full_memory(), test_contract_fields_present(), test_fail_triggers_reflector_memory_and_conditioned_retry(), test_full_history_conditions_each_trial_no_regression(), test_graph_runs_until_pass_and_stops(), fake_vector(), test_web_first_orders_web_tools_in_first_trial()

### Community 5 - "OneDrive Freshness Probe"
Cohesion: 0.14
Nodes (14): _parse(), probe_cited(), _probe_one(), FakeSource, _meta(), _state_with_origin(), test_budget_expiry_skips_reminder(), test_deleted_file_last_version_note() (+6 more)

### Community 6 - "System 1 Decision Node"
Cohesion: 0.07
Nodes (22): decide(), DecisionResult, fallback_route(), map_model_output(), _questions(), _test_cfg(), validate_output(), heuristic_classify() (+14 more)

### Community 7 - "Logging Setup Configuration"
Cohesion: 0.08
Nodes (25): D5: Redaction filter + DEBUG-only discipline at call sites, D6: Rotation + startup writability probe, D7: `status` additive field from a module-level `LoggingSetup`, Phase 2: Foundational (Blocking Prerequisites), configure_logging(), current_setup(), LoggingSetup, RedactionFilter (+17 more)

### Community 9 - "Agentic RAG MCP Server"
Cohesion: 0.08
Nodes (43): Spec-kit plan template, Spec-kit task list template, Specification Quality Checklist: Agentic RAG MCP Server, ask MCP Tool, fetch_url MCP Tool, graph.query MCP Tool (Graphify layer), MCP Tool Contracts: Agentic RAG MCP Server, search MCP Tool (+35 more)

### Community 10 - "Migration Error Handling"
Cohesion: 0.05
Nodes (32): D7: Migration — snapshot-absence defines the pending set; idempotent by construction, Implementation for User Story 2, Phase 8: Cross-Cutting — One-Time Migration (FR-016), DecisionLayerUnavailable, Err, ErrorCode, IngestionError, Ok (+24 more)

### Community 11 - "Spec-Kit Shell Helpers"
Cohesion: 0.13
Nodes (29): check-prerequisites.sh script, check_dir(), check_file(), find_specify_root(), format_speckit_command(), get_current_branch(), get_feature_paths(), get_invoke_separator() (+21 more)

### Community 12 - "Specialty Web Search"
Cohesion: 0.15
Nodes (12): _default_path(), load_profiles(), normalize_site(), resolve_profile(), profiles_file(), test_load_profiles_malformed_json(), test_load_profiles_missing_file(), test_load_profiles_valid_file() (+4 more)

### Community 13 - "OneDrive Contract Tests"
Cohesion: 0.11
Nodes (15): _add_onedrive(), call(), _fake_graph(), _server(), test_ask_response_frozen_fields_plus_additive_freshness(), test_existing_tools_canary_unchanged(), test_onedrive_embed_files_contract_shape(), test_onedrive_list_files_contract_shape() (+7 more)

### Community 14 - "OneDrive Test Fakes"
Cohesion: 0.06
Nodes (29): FakeAuth, FakeSource, FakeVectors, _item(), _mock_graph(), fake_get(), _pipeline(), _resolved() (+21 more)

### Community 15 - "Logging Design Decisions"
Cohesion: 0.13
Nodes (14): D10: Error handling — one binding matrix (first-class deliverable), D11: Test strategy — RED first, tmp-isolated, no network, D1: Programmatic setup, not dictConfig, D2: Framework logs via root propagation — uvicorn must not self-configure, D4: Default log path derives from `state_db`'s directory — test isolation for free, D8: Invalid level → WARN + default, never a crash, D9: DEBUG trace points (FR-004 / US3), Research: Application Log File with Leveled Logging (+6 more)

### Community 16 - "Logging and Tool Models"
Cohesion: 0.08
Nodes (21): EmbedOutcome (onedrive_embed_files per-file results), FileListingEntry (onedrive_list_files items), FreshnessSnapshot (origins.snapshot JSON), StalenessReminder (ask response `freshness_warnings[]` + answer-text suffix), Tool-level value shapes, Configuration (`[logging]` section in config.toml → Config fields), Data Model: Application Log File with Leveled Logging, Error taxonomy (binding mapping) (+13 more)

### Community 17 - "State Store Methods"
Cohesion: 0.13
Nodes (7): StateStore — new/changed methods, D3: Freshness snapshot — per-origin column, not per-source sync_state, Phase 2: Foundational (Blocking Prerequisites), _now(), StateStore, test_watcher_isolates_bad_source(), test_local_origins_never_probed()

### Community 18 - "OneDrive On-Demand Tests"
Cohesion: 0.12
Nodes (13): call(), _drive_graph(), fake_get(), _graph_spy(), _mutable_graph(), _server(), test_auth_completion_never_ingests(), test_connect_never_ingests_across_watcher_cycles() (+5 more)

### Community 19 - "Episodic Memory Records"
Cohesion: 0.18
Nodes (8): EpisodicMemory, _rec(), test_append_ordering_preserved(), test_memory_starts_empty_per_request(), test_no_cross_request_leakage(), test_record_serializes_all_fields(), test_union_deduplicates_terms_in_first_appearance_order(), test_union_missing_focus_is_full_history_not_latest()

### Community 20 - "Web Search Providers"
Cohesion: 0.15
Nodes (12): make_web_tool(), ProviderError, build_providers(), ExaProvider, SearxngProvider, TavilyProvider, web_search(), test_unconfigured_provider_raises() (+4 more)

### Community 21 - "OneDrive On-Demand Spec"
Cohesion: 0.05
Nodes (35): Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: OneDrive On-Demand Embedding with Staleness Reminder, Data Model: OneDrive On-Demand Embedding with Staleness Reminder, Error taxonomy (binding mapping), Origin/snapshot lifecycle (+27 more)

### Community 22 - "OneDrive Source Connector"
Cohesion: 0.12
Nodes (5): D1: Metadata-only listing — recursive `children` traversal, not delta-as-listing, D2: Embed file resolution — one call per file, path or item id, GraphBase, OneDriveSource, SharePointSource

### Community 23 - "Logging Integration Tests"
Cohesion: 0.20
Nodes (11): call(), _flush(), _info_lines(), _server(), test_debug_trace_end_to_end(), test_failures_logged_with_reasons(), test_rotation_caps_disk(), test_session_events_recorded_at_info() (+3 more)

### Community 24 - "One-Time Migration Tests"
Cohesion: 0.16
Nodes (9): FakeSource, FakeVectors, _legacy_state(), _pipeline(), _res(), test_migration_auth_expired_honest_and_retried(), test_migration_deleted_file_keeps_copy_and_retries(), test_migration_noop_without_legacy() (+1 more)

### Community 25 - "Server Transport Config"
Cohesion: 0.15
Nodes (5): D3: Prints convert to log records (no stdout capture hacks), _get(), init_config(), load_config(), main()

### Community 26 - "OneDrive Graph Auth"
Cohesion: 0.13
Nodes (8): D6 — Auth state machine, SourceAuthError, _onedrive_auth(), _onedrive_source(), ClientCredentialsAuth, GraphAuth, test_expired_credential_marks_source_degraded(), token()

### Community 27 - "Answer Synthesis"
Cohesion: 0.33
Nodes (3): citations(), synthesize(), SufficiencyExhausted

### Community 28 - "Rule-Based Evaluator"
Cohesion: 0.20
Nodes (9): evaluate(), _terms(), _ev(), test_full_coverage_with_citations_passes_with_high_score(), test_hit_count_is_scoring_input_not_verdict_gate(), test_identical_inputs_identical_outputs(), test_no_citable_evidence_caps_score_and_fails(), test_partial_coverage_fails_and_names_missing_terms() (+1 more)

### Community 29 - "Specialty Search Integration"
Cohesion: 0.20
Nodes (8): call(), FakeProvider, _server(), test_case_insensitive_profile_lookup(), test_hot_reload_new_profile_immediately_usable(), test_missing_profiles_file_honest_error(), test_results_filtered_to_matching_domains(), test_zero_scoped_results_honest_empty()

### Community 30 - "Specialty Search Checklist"
Cohesion: 0.15
Nodes (9): Dual-System Architecture, Constitution Compliance (ratified 2026-10-08), Content Quality, Feature Readiness, Requirement Completeness, Specification Quality Checklist: Specialty Web Search — Profile-Scoped Domain Search, Specialty Web Search Feature, FR-006: Substring domain filter (+1 more)

### Community 31 - "Fallback Provenance Tests"
Cohesion: 0.18
Nodes (9): call(), _live_cfg(), _median(), server(), test_fallback_latency_within_budget(), test_no_third_provenance_value(), test_outage_routes_via_fallback_and_marks_it(), test_recovery_next_request_uses_decision_node() (+1 more)

### Community 32 - "Web Research Integration"
Cohesion: 0.24
Nodes (10): call(), FakeProvider, _hits_by_url(), _server(), test_ask_live_web_evidence_uses_grouped_content(), test_every_hit_yields_content_mixed_paths(), test_forbidden_page_falls_back_marked_http_403(), test_normal_page_scraped_with_grouped_content() (+2 more)

### Community 33 - "Laya Runtime"
Cohesion: 0.35
Nodes (6): Config, get_agent(), _model_dir(), system_one(), _try_load(), warm_up()

### Community 35 - "Spec-Kit PowerShell Helpers"
Cohesion: 0.17
Nodes (15): Find-SpecifyRoot(), Format-SpecKitCommand(), Get-CurrentBranch(), Get-FeaturePathsEnv(), Get-InvokeSeparator(), Get-Python3Command(), Get-RepoRoot(), Resolve-SpecifyInitDir() (+7 more)

### Community 36 - "Web Research Design"
Cohesion: 0.16
Nodes (14): D1: HTTP client — reuse httpx, D2: HTML parsing — beautifulsoup4 + lxml (the only new dependencies), D3: Parallel page fetching — bounded thread pool, D4: SSRF guard — per-hop address resolution + ipaddress check, D5: Grouping rules — reference algorithm + spec bounds, D8: Configuration surface — [web.research] block in config.toml, FR-005: Document-order grouped section extraction, FR-008: Honest snippet fallback — never silently missing, never fabricated (+6 more)

### Community 37 - "Graph Connector Tests"
Cohesion: 0.21
Nodes (9): ExpiredAuth, FakeAuth, test_expired_token_propagates(), test_network_error_is_provider_error(), test_onedrive_list_files_returns_metadata(), test_sharepoint_401_raises_auth_error(), test_exa_timeout_raises_provider_error(), test_searxng_respects_limit() (+1 more)

### Community 38 - "OneDrive Ingestion Tasks"
Cohesion: 0.10
Nodes (20): Dependencies & Execution Order, Format: `[ID] [P?] [Story] Description`, Implementation for User Story 1, Implementation for User Story 2, Implementation for User Story 3, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 only) (+12 more)

### Community 39 - "Specialty Search Contract"
Cohesion: 0.22
Nodes (7): call(), FakeProvider, server(), test_existing_web_search_canary_unchanged(), test_specialty_profiles_returns_full_json(), test_specialty_search_invalid_profile_honest_error(), test_specialty_search_returns_only_matching_domains()

### Community 40 - "Agentic RAG Architecture"
Cohesion: 0.18
Nodes (9): AgenticRAG MCP sidecar (Dify compose service), Chunk entity (embedded segment, row in LanceDB), Document entity (canonical ingested item, deduplicated by content), OriginRef entity (one physical location of a Document), Source entity (connector config + health), CocoIndex [full] incremental pipeline, LanceDB embedded vector store, Local sentence-transformers embeddings (all-MiniLM-L6-v2) (+1 more)

### Community 41 - "Speckit Commands"
Cohesion: 0.50
Nodes (12): speckit.analyze Command, speckit.checklist Command, speckit.clarify Command, speckit.constitution Command, Project Constitution, speckit.converge Command, speckit.implement Command, speckit.plan Command (+4 more)

### Community 42 - "Speckit Workflows"
Cohesion: 0.32
Nodes (12): Speckit Analyze Workflow, Speckit Checklist Workflow, Speckit Clarify Workflow, Speckit Constitution Workflow, Speckit Converge Workflow, Speckit Implement Workflow, Speckit Plan Workflow, Speckit Specify Workflow (+4 more)

### Community 43 - "MCP Server Core"
Cohesion: 0.20
Nodes (3): NotFoundError, Watcher, SqliteSource

### Community 44 - "Web Research Contract"
Cohesion: 0.35
Nodes (7): call(), FakeProvider, _server(), test_web_research_all_engines_down_honest_empty(), test_web_research_limit_capped_at_max_pages(), test_web_research_schema_v2(), test_web_search_stays_byte_identical_without_engine_field()

### Community 45 - "Reflexion Quickstart Tests"
Cohesion: 0.19
Nodes (5): call(), call(), server(), test_live_web_route_leads_with_web_tools(), test_multi_part_question_covers_all_parts_with_reflections()

### Community 46 - "Decision Routing Tests"
Cohesion: 0.29
Nodes (7): call(), direct_output(), server(), test_decision_contains_only_structured_values(), test_direct_route_served_in_one_step(), test_forced_mode_still_records_decision(), test_source_management_route_gives_guidance_without_operations()

### Community 47 - "OneDrive Ingestion Spec"
Cohesion: 0.10
Nodes (17): Constitution Compliance (ratified 2026-10-08), Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: OneDrive Ingestion — Full Pipeline with Auto-Update, Assumptions, Edge Cases (+9 more)

### Community 48 - "Port Alignment Spec"
Cohesion: 0.08
Nodes (24): Aligned Port Convention (28080:28080, 28888:28888), Sidecar Compose (28080:28080), Dify Sidecar Server (aligned port 28080), Network Topology (Dify ↔ AgenticRAG ↔ Host), Constitution Compliance (ratified 2026-10-08), Content Quality, Feature Readiness, Notes (+16 more)

### Community 49 - "MCP Contract Tests"
Cohesion: 0.31
Nodes (7): call(), server(), test_ask_no_documents_returns_no_fabrication(), test_bad_source_type_raises_not_found(), test_graph_query_disabled_by_default(), test_status_shape(), test_unknown_source_remove_is_graceful()

### Community 50 - "State Snapshot Tests"
Cohesion: 0.38
Nodes (6): _origin(), _store(), test_onedrive_origins_without_snapshot(), test_origins_for_document(), test_snapshot_rejects_mismatched_item_id(), test_snapshot_roundtrip_and_invariant()

### Community 51 - "Logging Contract Tests"
Cohesion: 0.33
Nodes (5): call(), _server(), test_config_level_from_toml(), test_status_gains_additive_logging_field(), test_status_reflects_debug_level()

### Community 52 - "End-to-End Tests"
Cohesion: 0.33
Nodes (6): call(), server(), test_deep_path_budget_exhaustion_marks_low_confidence(), test_deep_path_multi_tool_trace(), test_full_flow_ingest_and_ask(), test_incremental_add_update_delete()

### Community 53 - "OneDrive On-Demand Tools"
Cohesion: 0.13
Nodes (20): Contract: OneDrive On-Demand Tools & Staleness Reminder, Tool: `onedrive_embed_files` (NEW), Tool: `onedrive_list_files` (NEW), Tool: `sources_add(type:"onedrive")` (EXISTING — message values change), Tool: `sources_auth` (EXISTING — no-sync semantics), Tool: `sources_sync` (EXISTING — onedrive notice), Complexity Tracking, Constitution Check (+12 more)

### Community 54 - "Success Criteria Tests"
Cohesion: 0.36
Nodes (4): call(), server(), test_sc001_002_003_over_100_questions(), test_sc005_budget_exhausted_always_flagged_low()

### Community 55 - "Implementation Task Plan"
Cohesion: 0.10
Nodes (20): Dependencies & Execution Order, Format: `[ID] [P?] [Story] Description`, Implementation for User Story 4, Implementation Strategy, Incremental Delivery, MVP First (US1 + US2), Notes, Parallel Example: User Story 2 (+12 more)

### Community 56 - "AgenticRAG Constitution"
Cohesion: 0.29
Nodes (7): AgenticRAG Constitution, Contract Preservation (Principle I), Honest Answers (Principle IV), Minimal Dependencies (Principle III), Spec-Driven Replacement (Principle V), Tests-First (Principle II), Speckit Full SDD Cycle (specify - plan - tasks - implement)

### Community 57 - "Test Fixture Corpus"
Cohesion: 0.29
Nodes (6): broken.pdf fixture (corrupt file, skip-with-reason path), Test fixture corpus (PDF/DOCX/XLSX/PPTX/SQLite/audio), notes.sqlite3 fixture (SQLite source connector), audio/silence.wav fixture (no-speech path), faster-whisper local audio transcription, Scenario 5 - Error handling assertions

### Community 58 - "Ask Response Contract"
Cohesion: 0.32
Nodes (4): call(), server(), test_all_fields_present_on_every_response(), test_decision_invariants_on_both_provenances()

### Community 59 - "Port Alignment Tasks"
Cohesion: 0.11
Nodes (18): Dependencies & Execution Order, Format: `[ID] [P?] [Story] Description`, Implementation for User Story 1, Implementation for User Story 2, Implementation for User Story 3, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 only) (+10 more)

### Community 60 - "OneDrive Ingestion Data Model"
Cohesion: 0.11
Nodes (16): Data Model: OneDrive Ingestion, Entities, File format filtering (same as local_folder), GraphFileItem, OneDriveSourceConfig, OneDriveSyncState, Request lifecycle, TokenCache (+8 more)

### Community 61 - "CocoIndex Code Settings"
Cohesion: 0.67
Nodes (3): CocoIndex Code Settings, graphify Command, graphify Skill

### Community 62 - "SQLite State Tools"
Cohesion: 0.16
Nodes (4): make_sql_tool(), corpus(), test_sql_tool_no_text_column(), test_sql_tool_reads_rows()

### Community 71 - "OneDrive Auth Spec"
Cohesion: 0.25
Nodes (16): Summary, Functional Requirements, Superseded behaviors (removed — spec 006, Constitution V), Test matrix (contract + unit + integration — every row is a named test), Technical Context, D10: Test strategy — supersede in place, pin the invariants, D6: Watcher — onedrive branch deleted, not skipped, Implementation for User Story 1 (+8 more)

### Community 74 - "Reflexion LangGraph Flow"
Cohesion: 0.22
Nodes (9): ReflectionRecord, _actor(), _after_evaluator(), _after_memory(), _build_graph(), _evaluator(), _memory_node(), _self_reflector() (+1 more)

### Community 75 - "Web Search Scrape Tasks"
Cohesion: 0.12
Nodes (16): Dependencies & Execution Order, Format: `[ID] [P?] [Story] Description`, Implementation for User Story 1, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 only), Notes, Parallel Opportunities (+8 more)

### Community 76 - "OneDrive Staleness Research"
Cohesion: 0.17
Nodes (15): Error-response matrix (single source of truth), Tool: `ask` (EXISTING — additive field), D4: Staleness probe — bounded parallel, identity by item id, honest outcomes, D5: Staleness reminder content — timestamps + actionable identifier, D8: `sources_auth` — keep non-blocking device flow, drop the sync trigger, D9: Error handling — one honest per-file outcome model everywhere, Research: OneDrive On-Demand Embedding with Staleness Reminder, Implementation for User Story 3 (+7 more)

### Community 77 - "Port Alignment Quickstart"
Cohesion: 0.13
Nodes (13): Before → After, Contract: Port Alignment, Invariants, What does NOT change, Notes, Prerequisites, Quickstart: Port Alignment Validation, S1 — Sidecar aligned port (FR-001 / SC-001) (+5 more)

### Community 84 - "OneDrive Auth Contract"
Cohesion: 0.14
Nodes (15): Contract: OneDrive Source + `sources_auth` MCP Tools, Invariants, Request, Request, Response (already authenticated), Response (existing token, immediate sync), Response (no token, needs sign-in), Response (sign-in completed — checked after user returns) (+7 more)

### Community 91 - "Edge Case Tests"
Cohesion: 0.23
Nodes (6): call(), server(), test_budget_exhaustion_low_confidence(), test_concurrent_queries_consistent(), test_corrupt_and_encrypted_files_skipped_not_blocking(), test_laya_down_falls_back_and_reports()

### Community 92 - "RL Agent Inference"
Cohesion: 0.16
Nodes (4): amp_dtype(), build_model(), collate_items(), predict_items()

### Community 93 - "Web Research Implementation"
Cohesion: 0.15
Nodes (12): Implementation for User Story 2, Implementation for User Story 3, Phase 4: User Story 2 — Grouped Extraction, Bounds, Fallbacks, Evidence Upgrade (Priority: P1), Phase 5: User Story 3 — Human-Readable Rendering (Priority: P3), Phase 6: Polish & Cross-Cutting Concerns, Tests for User Story 2 (all RED before the implementations), Tests for User Story 3, S6 — Contract freeze (SC-005) (+4 more)

### Community 94 - "Specialty Search Plan"
Cohesion: 0.20
Nodes (14): Notes, Complexity Tracking, Constitution Check, Implementation Plan: Specialty Web Search — Profile-Scoped Domain Search, Summary, Technical Context, S1 — `specialty_profiles()` listing (FR-009), Implementation for User Story 1 (+6 more)

### Community 95 - "Specialty Search Quickstart"
Cohesion: 0.14
Nodes (12): Specialty Search Tool Contract, ProfileFile (JSON, hot-reload), SpecialtyProfile entity, Notes, Prerequisites, Quickstart: Specialty Web Search Validation, S2 — `specialty_search` scoped results (FR-005/006 / SC-001), S3 — Honest errors (FR-007 / SC-003) (+4 more)

### Community 96 - "Specialty Search Tasks"
Cohesion: 0.14
Nodes (13): Dependencies & Execution Order, Format: `[ID] [P?] [Story] Description`, Implementation for User Story 2, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 only), Notes, Parallel Opportunities (+5 more)

### Community 97 - "Provider Chain Tests"
Cohesion: 0.29
Nodes (9): search_all(), FakeProvider, _hit(), test_all_engines_down_honest_empty_with_error(), test_duplicate_urls_across_engines_dedup_keeps_first_ranking(), test_engine_down_next_engine_serves(), test_healthy_engine_zero_hits_is_honest_empty_not_error(), test_no_providers_configured_is_error_state() (+1 more)

### Community 98 - "Logging Task Plan"
Cohesion: 0.15
Nodes (13): Format: `[ID] [P?] [Story] Description`, Implementation for User Story 1, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 Only), Notes, Parallel Example: User Story 1, Parallel Team Strategy (+5 more)

### Community 99 - "Research Extraction Tests"
Cohesion: 0.24
Nodes (6): extract_sections(), _html(), test_dirty_markup_noise_rules(), test_js_only_page_yields_no_sections_without_crashing(), test_ordered_page_sections_preserve_document_order(), test_oversized_page_truncated_at_bound_and_flagged()

### Community 100 - "OneDrive Ingestion Plan"
Cohesion: 0.17
Nodes (11): Complexity Tracking, Constitution Check, Documentation (this feature), Implementation Plan: OneDrive Ingestion — Full Pipeline with Auto-Update, Project Structure, Source Code (repository root), Technical Context, User-managed files (not committed) (+3 more)

### Community 102 - "RL Data Encoding"
Cohesion: 0.25
Nodes (5): build_sequence(), encode_record(), episode_prefix_lengths(), render_options(), serialize_state()

### Community 103 - "OneDrive Ingestion Research"
Cohesion: 0.22
Nodes (8): D1 — Delta queries for incremental sync (decided in Clarifications), D2 — Recursive folder traversal (initial sync), D3 — Non-blocking sources_auth flow, D4 — File download, D5 — File size cap, D7 — Error handling matrix, D9 — Config surface, Research: OneDrive Ingestion

### Community 104 - "Logging Status Contract"
Cohesion: 0.31
Nodes (9): Configuration surface, Contract: Logging Setup, Status Field & Error Handling, Error-response matrix (single source of truth), Test matrix (contract + unit + integration — every row is a named test), Tool: `status` (EXISTING — additive field), Implementation for User Story 2, Phase 4: User Story 2 — Operator-configurable level + status exposure (Priority: P2), Tests for User Story 2 (+1 more)

### Community 105 - "Logging Implementation Plan"
Cohesion: 0.22
Nodes (9): Complexity Tracking, Constitution Check, Documentation (this feature), Implementation Plan: Application Log File with Leveled Logging, Project Structure, Source Code (repository root), Summary, Technical Context (+1 more)

### Community 106 - "Logging Feature Spec"
Cohesion: 0.22
Nodes (9): Assumptions, Clarifications, Feature Specification: Application Log File with Leveled Logging, Functional Requirements, Key Entities, Measurable Outcomes, Requirements *(mandatory)*, Session 2026-10-12 (+1 more)

### Community 107 - "Question Planner"
Cohesion: 0.31
Nodes (4): decompose(), test_planner_default_vector(), test_planner_multi_part(), test_planner_sql_keyword_routes_sql()

### Community 108 - "RL Agent Confidence"
Cohesion: 0.25
Nodes (3): RLAgent, confidence_from_probs(), temp_bucket()

### Community 110 - "Logging Checklist"
Cohesion: 0.29
Nodes (5): Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: Application Log File with Leveled Logging

### Community 111 - "Research Page Renderer"
Cohesion: 0.38
Nodes (4): render_page(), test_render_fallback_default_marker_when_no_snippet(), test_render_fallback_shows_snippet_with_visible_marker(), test_render_mirrors_grouped_structure_in_order()

### Community 114 - "Domain Filtering"
Cohesion: 0.33
Nodes (4): filter_by_domains(), test_filter_by_domains_empty_input(), test_filter_by_domains_no_matches(), test_filter_by_domains_substring_match()

### Community 115 - "Dify Specialty Agent"
Cohesion: 0.40
Nodes (4): Dify Chatflow with 13 MCP Tools, 13 MCP Tools, specialty_profiles MCP tool, specialty_search MCP tool

### Community 117 - "Logging Quickstart"
Cohesion: 0.40
Nodes (5): 1. Automated validation (CI-grade), 2. Live check (running sidecar), Expected outcomes summary, Prerequisites, Quickstart: Application Log File with Leveled Logging

### Community 118 - "Logging User Stories"
Cohesion: 0.40
Nodes (5): Edge Cases, User Scenarios & Testing *(mandatory)*, User Story 1 - Every event recorded to a persistent log file with level semantics (Priority: P1), User Story 2 - Operator-configurable level without code changes (Priority: P2), User Story 3 - DEBUG traces execution flow to the problem's source (Priority: P2)

### Community 119 - "Task Dependencies"
Cohesion: 0.40
Nodes (5): Dependencies & Execution Order, Parallel Opportunities, Phase Dependencies, User Story Independent Tests, Within Each User Story

### Community 122 - "Feature Documentation"
Cohesion: 0.50
Nodes (4): Documentation (this feature), Project Structure, Source Code (repository root), User-managed file (not committed to the repo)

### Community 123 - "Site-Scoped Query Builder"
Cohesion: 0.50
Nodes (3): construct_scoped_query(), test_construct_scoped_query_multiple_sites(), test_construct_scoped_query_single_site()

## Knowledge Gaps
- **54 isolated node(s):** `agentic-rag-mcp`, `Speckit Full SDD Cycle (specify - plan - tasks - implement)`, `specialty_profiles MCP tool`, `specialty_search MCP tool`, `routing/fallback.py (DEMOTED: keyword heuristic, outage-only)` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 707 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_server()` connect `Logging Design Decisions` to `Reflexion Graph Agent`, `OneDrive Freshness Probe`, `System 1 Decision Node`, `Logging Setup Configuration`, `Vector Store Wrapper`, `Migration Error Handling`, `Specialty Web Search`, `OneDrive Contract Tests`, `Logging and Tool Models`, `State Store Methods`, `OneDrive On-Demand Tests`, `Web Search Providers`, `Logging Integration Tests`, `Server Transport Config`, `OneDrive Graph Auth`, `Specialty Search Integration`, `Fallback Provenance Tests`, `Web Research Integration`, `Laya Runtime`, `Specialty Search Contract`, `MCP Server Core`, `Web Research Contract`, `Reflexion Quickstart Tests`, `Decision Routing Tests`, `MCP Contract Tests`, `Logging Contract Tests`, `End-to-End Tests`, `OneDrive On-Demand Tools`, `Success Criteria Tests`, `Ask Response Contract`, `OneDrive Auth Spec`, `OneDrive Staleness Research`, `OneDrive Auth Contract`, `Edge Case Tests`, `Web Research Implementation`, `Specialty Search Plan`, `Provider Chain Tests`, `Logging Status Contract`, `Research Page Renderer`, `Local Embeddings`, `Domain Filtering`, `Site-Scoped Query Builder`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `build_server()` (e.g. with `D7: Migration — snapshot-absence defines the pending set; idempotent by construction` and `Phase 8: Cross-Cutting — One-Time Migration (FR-016)`) actually correct?**
  _`build_server()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `agentic-rag-mcp`, `Speckit Full SDD Cycle (specify - plan - tasks - implement)`, `specialty_profiles MCP tool` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Prerequisite Check CLI` be split into smaller, more focused modules?**
  _Cohesion score 0.05777491408934708 - nodes in this community are weakly interconnected._
- **Why does `sources_auth()` connect `OneDrive Auth Spec` to `OneDrive Ingestion Plan`, `OneDrive Ingestion Tasks`, `MCP Server Core`, `OneDrive Staleness Research`, `OneDrive Ingestion Spec`, `Logging Design Decisions`, `OneDrive Auth Contract`, `OneDrive On-Demand Tools`, `OneDrive Graph Auth`, `OneDrive Ingestion Data Model`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `ProviderError` (e.g. with `Error taxonomy (binding mapping)` and `D9: Error handling — one honest per-file outcome model everywhere`) actually correct?**
  _`ProviderError` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Should `RL Agent Shared Code` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._