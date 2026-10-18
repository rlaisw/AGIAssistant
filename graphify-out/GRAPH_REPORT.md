# Graph Report - AGIAssistant  (2026-10-18)

## Corpus Check
- 293 files · ~254,519 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 12, .css 3, .code-workspace 2)

## Summary
- 3087 nodes · 5090 edges · 212 communities (175 shown, 37 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 695 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6585322f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- common.py
- SSRF Guarded Fetch
- rl_common.py
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
- sources_auth
- Port Alignment Spec
- MCP Contract Tests
- State Snapshot Tests
- Logging Contract Tests
- toolbar
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
- shadcn/ui
- Spec-kit feature specification template
- Agentic RAG MCP
- Reflexion LangGraph Flow
- Web Search Scrape Tasks
- Data Model: OneDrive On-Demand Embedding with Staleness Reminder
- Port Alignment Quickstart
- Local Folder Q&A
- Incremental Update
- Multi-source Deep Research
- MCP Client Wiring
- OneDrive Auth Contract
- Edge Case Tests
- form
- form
- Specialty Search Plan
- Specialty Search Quickstart
- Specialty Search Tasks
- Provider Chain Tests
- Logging Task Plan
- Research Extraction Tests
- page.tsx
- HTTP Test Server
- select
- Button
- status
- Per-component notes
- Feature Specification: Application Log File with Leveled Logging
- Question Planner
- dropdown-menu.tsx
- SSRF Web Research
- Per-component notes
- Research Page Renderer
- Component Composition
- Separator
- Domain Filtering
- Dify Specialty Agent
- package.json
- components.json
- create_new_feature.py
- select
- compilerOptions
- Reflexion End-State Tests
- Feature Documentation
- Site-Scoped Query Builder
- AGENTS.md
- dropdown-menu (Radix `DropdownMenu` → Base UI `Menu`)
- dropdown-menu (Radix `DropdownMenu` → Base UI `Menu`)
- logging_setup.py
- loop
- layout.tsx
- agent/skills/shadcn/scripts/showcase-coverage.mjs
- json
- check_prerequisites.py
- context-menu (Radix `ContextMenu` → Base UI `ContextMenu`)
- navigation-menu (Radix `NavigationMenu` → Base UI `NavigationMenu`)
- Customization & Theming
- navigation-menu (Radix `NavigationMenu` → Base UI `NavigationMenu`)
- Customization & Theming
- dependencies
- agent/skills/migrate-radix-to-base/disclosure.md
- The Design System Page
- Styling & Customization
- The Design System Page
- Styling & Customization
- alert-dialog
- agent/skills/shadcn/assets/showcase/color-pair.tsx
- Design Systems from DESIGN.md
- Tools
- .agents/skills/migrate-radix-to-base/form-controls.md
- alert-dialog
- Design Systems from DESIGN.md
- Tools
- setup_tasks.py
- toast
- popover
- Page
- Component Composition
- popover
- markdown.tsx
- devDependencies
- Quickstart: OneDrive On-Demand Embedding with Staleness Reminder
- toolbar
- tooltip
- dialog
- Target wrapper shapes (golden-derived specifics)
- add
- toast
- tooltip
- dialog
- Target wrapper shapes (golden-derived specifics)
- test_decider_engine.py
- accordion
- context-menu (Radix `ContextMenu` → Base UI `ContextMenu`)
- hover-card → preview-card
- Commands
- hover-card → preview-card
- Commands
- tabs
- Step 4: Map Tokens to the Theme
- Foundations
- Registry Authoring and Addresses
- Base vs Radix
- Chat & Messaging
- Step 4: Map Tokens to the Theme
- Foundations
- Registry Authoring and Addresses
- Base vs Radix
- Quickstart: OneDrive Ingestion Validation
- heuristic_classify
- Class-string rewrites (layer 2)
- collapsible
- slider
- Radix UI -> Base UI migration
- Class-string rewrites (layer 2)
- slider
- Radix UI -> Base UI migration
- scripts
- Consumer-side prop changes (call sites, not wrappers)
- radio-group
- onedrive_freshness.py
- shadcn CLI Reference
- shadcn CLI Reference
- route.ts
- Next.js template
- Dependencies & Execution Order
- agent/skills/migrate-radix-to-base/overlays.md
- ai-chat-landing/AGENTS.md
- .agents/skills/migrate-radix-to-base/overlays.md
- postcss.config.mjs

## God Nodes (most connected - your core abstractions)
1. `build_server()` - 80 edges
2. `ProviderError` - 41 edges
3. `StateStore` - 40 edges
4. `Config` - 33 edges
5. `SourceAuthError` - 33 edges
6. `sources_auth()` - 30 edges
7. `Button()` - 26 edges
8. `ask()` - 25 edges
9. `status()` - 25 edges
10. `loop()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Code and tool output use CodeBlock` --references--> `wrap()`  [INFERRED]
  ai-chat-landing/agent/skills/shadcn/rules/chat.md → src/agentic_rag_mcp/errors.py
- `Code and tool output use CodeBlock` --references--> `wrap()`  [INFERRED]
  ai-chat-landing/.agents/skills/shadcn/rules/chat.md → src/agentic_rag_mcp/errors.py
- `Tabs.List → Tabs.List` --references--> `loop()`  [INFERRED]
  ai-chat-landing/agent/skills/migrate-radix-to-base/disclosure.md → src/agentic_rag_mcp/ingestion/watchers.py
- `ToggleGroup.Root → ToggleGroup` --references--> `loop()`  [INFERRED]
  ai-chat-landing/agent/skills/migrate-radix-to-base/disclosure.md → src/agentic_rag_mcp/ingestion/watchers.py
- `Toolbar.Root → Toolbar.Root` --references--> `loop()`  [INFERRED]
  ai-chat-landing/agent/skills/migrate-radix-to-base/disclosure.md → src/agentic_rag_mcp/ingestion/watchers.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Dual-System Request Flow: System 1 decision → FR-005 route mapping → execution path → ask response contract** — specs_002_laya_reflexion_nodes_spec_system_1_decision_node, specs_002_laya_reflexion_nodes_spec_fr005_route_mapping, specs_002_laya_reflexion_nodes_spec_system_2_reflexion_graph, specs_002_laya_reflexion_nodes_contracts_ask_response_ask_tool_contract [EXTRACTED 1.00]
- **Supersedes Replacement Scope: OLD components → NEW dual-system design** — specs_002_laya_reflexion_nodes_spec_single_label_classifier, specs_002_laya_reflexion_nodes_spec_keyword_heuristic_fallback, specs_002_laya_reflexion_nodes_spec_monolithic_deliberation_loop, specs_002_laya_reflexion_nodes_spec_hit_count_sufficiency_gate, specs_002_laya_reflexion_nodes_spec_system_1_decision_node, specs_002_laya_reflexion_nodes_spec_system_2_reflexion_graph, specs_002_laya_reflexion_nodes_spec_evaluator_stage [EXTRACTED 1.00]
- **System 2 Reflexion Loop: Actor → Evaluator → Self-Reflector → Episodic Memory** — specs_002_laya_reflexion_nodes_spec_actor_stage, specs_002_laya_reflexion_nodes_spec_evaluator_stage, specs_002_laya_reflexion_nodes_spec_self_reflector_stage, specs_002_laya_reflexion_nodes_data_model_episodicmemory, specs_002_laya_reflexion_nodes_spec_system_2_reflexion_graph [EXTRACTED 1.00]
- **Incremental ingestion pipeline (CocoIndex change detection into LanceDB chunks with dedup by content hash)** — specs_001_agentic_rag_mcp_plan_cocoindex_pipeline, specs_001_agentic_rag_mcp_plan_lancedb_vector_store, specs_001_agentic_rag_mcp_data_model_document, specs_001_agentic_rag_mcp_data_model_chunk, specs_001_agentic_rag_mcp_data_model_source [INFERRED 0.95]
- **System 1/System 2 question routing (Laya decision layer steering between fast retrieval and the LangGraph deliberative loop)** — specs_001_agentic_rag_mcp_research_d5_laya_routing, specs_001_agentic_rag_mcp_plan_langgraph_deliberative_loop [INFERRED 0.95]

## Communities (212 total, 37 thin omitted)

### Community 0 - "common.py"
Cohesion: 0.19
Nodes (19): _conventional_template(), find_specify_root(), format_speckit_command(), get_current_branch(), get_feature_paths(), get_invoke_separator(), get_repo_root(), _is_safe_component() (+11 more)

### Community 1 - "SSRF Guarded Fetch"
Cohesion: 0.16
Nodes (10): guarded_get(), ScrapeBlocked, _Resp, test_private_destinations_refused(), test_public_ip_allowed_and_returned(), fake_get(), test_redirect_chain_capped(), fake_get() (+2 more)

### Community 2 - "rl_common.py"
Cohesion: 0.05
Nodes (21): RLAgent, amp_dtype(), aurc(), auroc(), build_model(), build_sequence(), collate_items(), confidence_from_probs() (+13 more)

### Community 3 - "Dual-System Workflow Contracts"
Cohesion: 0.07
Nodes (41): Specification Quality Checklist: Dual-System Workflow, ask MCP Tool Response Contract (preserved fields + decision/reflections extensions), Pre-existing Contract Test Suite (tests/contract/), Dify Chatflow (client consumer of the ask tool), Contract: ask Tool Response, decide(question) → DecisionResult (System 1 decision node operation), Decision Primitives: choice, score, noul (one-pass three-question batch), Contract: System 1 Decision Schema (+33 more)

### Community 4 - "Reflexion Graph Agent"
Cohesion: 0.14
Nodes (8): ReflexionAgent, test_budget_exhaustion_low_confidence_and_full_memory(), test_contract_fields_present(), test_fail_triggers_reflector_memory_and_conditioned_retry(), test_full_history_conditions_each_trial_no_regression(), test_graph_runs_until_pass_and_stops(), fake_vector(), test_web_first_orders_web_tools_in_first_trial()

### Community 5 - "OneDrive Freshness Probe"
Cohesion: 0.17
Nodes (13): probe_cited(), FakeSource, _meta(), _state_with_origin(), test_budget_expiry_skips_reminder(), test_deleted_file_last_version_note(), test_local_origins_never_probed(), test_probe_auth_failure_marks_degraded_no_reminder() (+5 more)

### Community 6 - "System 1 Decision Node"
Cohesion: 0.12
Nodes (16): decide(), DecisionResult, fallback_route(), map_model_output(), _questions(), _test_cfg(), validate_output(), _result() (+8 more)

### Community 7 - "Logging Setup Configuration"
Cohesion: 0.13
Nodes (17): _cfg(), _configure(), _emit(), _file_text(), test_console_mirror_parity(), test_current_setup_fallback_shape(), test_disabled_level_lazy(), test_framework_logger_reaches_file() (+9 more)

### Community 9 - "Agentic RAG MCP Server"
Cohesion: 0.08
Nodes (43): Spec-kit plan template, Spec-kit task list template, Specification Quality Checklist: Agentic RAG MCP Server, ask MCP Tool, fetch_url MCP Tool, graph.query MCP Tool (Graphify layer), MCP Tool Contracts: Agentic RAG MCP Server, search MCP Tool (+35 more)

### Community 10 - "Migration Error Handling"
Cohesion: 0.06
Nodes (27): DecisionLayerUnavailable, Err, ErrorCode, IngestionError, Ok, RagError, wrap(), content_hash() (+19 more)

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
Cohesion: 0.09
Nodes (20): D7: Migration — snapshot-absence defines the pending set; idempotent by construction, Implementation for User Story 2, Phase 8: Cross-Cutting — One-Time Migration (FR-016), D10: Error handling — one binding matrix (first-class deliverable), D11: Test strategy — RED first, tmp-isolated, no network, D1: Programmatic setup, not dictConfig, D2: Framework logs via root propagation — uvicorn must not self-configure, D3: Prints convert to log records (no stdout capture hacks) (+12 more)

### Community 16 - "Logging and Tool Models"
Cohesion: 0.14
Nodes (9): FeatureDisabledError, GraphifySearch, graph_query(), test_unconfigured_provider_raises(), test_cli_failure_is_provider_error(), test_disabled_by_default(), test_enabled_but_graph_missing(), test_explain_shells_out() (+1 more)

### Community 17 - "State Store Methods"
Cohesion: 0.14
Nodes (5): StateStore — new/changed methods, D3: Freshness snapshot — per-origin column, not per-source sync_state, Phase 2: Foundational (Blocking Prerequisites), _now(), StateStore

### Community 18 - "OneDrive On-Demand Tests"
Cohesion: 0.12
Nodes (13): call(), _drive_graph(), fake_get(), _graph_spy(), _mutable_graph(), _server(), test_auth_completion_never_ingests(), test_connect_never_ingests_across_watcher_cycles() (+5 more)

### Community 19 - "Episodic Memory Records"
Cohesion: 0.18
Nodes (8): EpisodicMemory, _rec(), test_append_ordering_preserved(), test_memory_starts_empty_per_request(), test_no_cross_request_leakage(), test_record_serializes_all_fields(), test_union_deduplicates_terms_in_first_appearance_order(), test_union_missing_focus_is_full_history_not_latest()

### Community 20 - "Web Search Providers"
Cohesion: 0.15
Nodes (11): make_web_tool(), ProviderError, build_providers(), ExaProvider, SearxngProvider, TavilyProvider, web_search(), test_web_tool_all_down_returns_empty() (+3 more)

### Community 21 - "OneDrive On-Demand Spec"
Cohesion: 0.09
Nodes (21): Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: OneDrive On-Demand Embedding with Staleness Reminder, Assumptions, Clarifications, Edge Cases (+13 more)

### Community 22 - "OneDrive Source Connector"
Cohesion: 0.11
Nodes (7): Item Definitions, Item Definitions, D1: Metadata-only listing — recursive `children` traversal, not delta-as-listing, D2: Embed file resolution — one call per file, path or item id, GraphBase, OneDriveSource, SharePointSource

### Community 23 - "Logging Integration Tests"
Cohesion: 0.20
Nodes (11): call(), _flush(), _info_lines(), _server(), test_debug_trace_end_to_end(), test_failures_logged_with_reasons(), test_rotation_caps_disk(), test_session_events_recorded_at_info() (+3 more)

### Community 24 - "One-Time Migration Tests"
Cohesion: 0.16
Nodes (9): FakeSource, FakeVectors, _legacy_state(), _pipeline(), _res(), test_migration_auth_expired_honest_and_retried(), test_migration_deleted_file_keeps_copy_and_retries(), test_migration_noop_without_legacy() (+1 more)

### Community 25 - "Server Transport Config"
Cohesion: 0.14
Nodes (5): Technical Context, _get(), init_config(), load_config(), main()

### Community 26 - "OneDrive Graph Auth"
Cohesion: 0.14
Nodes (8): D6 — Auth state machine, Error taxonomy (binding mapping), SourceAuthError, _onedrive_auth(), ClientCredentialsAuth, GraphAuth, test_expired_credential_marks_source_degraded(), token()

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
Cohesion: 0.18
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
Cohesion: 0.24
Nodes (3): NotFoundError, Watcher, SqliteSource

### Community 44 - "Web Research Contract"
Cohesion: 0.35
Nodes (7): call(), FakeProvider, _server(), test_web_research_all_engines_down_honest_empty(), test_web_research_limit_capped_at_max_pages(), test_web_research_schema_v2(), test_web_search_stays_byte_identical_without_engine_field()

### Community 45 - "Reflexion Quickstart Tests"
Cohesion: 0.12
Nodes (11): call(), call(), server(), test_deep_path_budget_exhaustion_marks_low_confidence(), test_deep_path_multi_tool_trace(), test_full_flow_ingest_and_ask(), test_incremental_add_update_delete(), call() (+3 more)

### Community 46 - "Decision Routing Tests"
Cohesion: 0.29
Nodes (7): call(), direct_output(), server(), test_decision_contains_only_structured_values(), test_direct_route_served_in_one_step(), test_forced_mode_still_records_decision(), test_source_management_route_gives_guidance_without_operations()

### Community 47 - "sources_auth"
Cohesion: 0.07
Nodes (40): Constitution Compliance (ratified 2026-10-08), Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: OneDrive Ingestion — Full Pipeline with Auto-Update, Complexity Tracking, Constitution Check (+32 more)

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

### Community 52 - "toolbar"
Cohesion: 0.04
Nodes (46): accordion, Accordion.Content → Accordion.Panel, Accordion.Header → Accordion.Header, Accordion.Item → Accordion.Item, Accordion.Root → Accordion.Root, Accordion.Trigger → Accordion.Trigger, Base UI only props worth knowing, Base UI only props worth knowing (+38 more)

### Community 53 - "OneDrive On-Demand Tools"
Cohesion: 0.09
Nodes (37): Contract: OneDrive On-Demand Tools & Staleness Reminder, Error-response matrix (single source of truth), Test matrix (contract + unit + integration — every row is a named test), Tool: `ask` (EXISTING — additive field), Tool: `onedrive_embed_files` (NEW), Tool: `onedrive_list_files` (NEW), Tool: `sources_add(type:"onedrive")` (EXISTING — message values change), Tool: `sources_auth` (EXISTING — no-sync semantics) (+29 more)

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
Cohesion: 0.18
Nodes (8): Data Model: OneDrive Ingestion, Entities, File format filtering (same as local_folder), GraphFileItem, OneDriveSourceConfig, OneDriveSyncState, Request lifecycle, TokenCache

### Community 61 - "CocoIndex Code Settings"
Cohesion: 0.67
Nodes (3): CocoIndex Code Settings, graphify Command, graphify Skill

### Community 62 - "SQLite State Tools"
Cohesion: 0.11
Nodes (7): make_sql_tool(), Embedder, corpus(), test_sql_tool_no_text_column(), test_sql_tool_reads_rows(), test_watcher_isolates_bad_source(), test_watcher_sync_once_local()

### Community 71 - "shadcn/ui"
Cohesion: 0.10
Nodes (20): Component Docs, Examples, and Usage, Current Project Context, Design Systems from DESIGN.md, Detailed References, Key Fields, Key Patterns, Principles, Quick Reference (+12 more)

### Community 74 - "Reflexion LangGraph Flow"
Cohesion: 0.20
Nodes (9): ReflectionRecord, _actor(), _after_evaluator(), _after_memory(), _build_graph(), _evaluator(), _memory_node(), _self_reflector() (+1 more)

### Community 75 - "Web Search Scrape Tasks"
Cohesion: 0.10
Nodes (21): Format: `[ID] [P?] [Story] Description`, Implementation for User Story 1, Implementation for User Story 2, Implementation for User Story 3, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 only), Notes (+13 more)

### Community 76 - "Data Model: OneDrive On-Demand Embedding with Staleness Reminder"
Cohesion: 0.09
Nodes (22): Data Model: OneDrive On-Demand Embedding with Staleness Reminder, EmbedOutcome (onedrive_embed_files per-file results), FileListingEntry (onedrive_list_files items), FreshnessSnapshot (origins.snapshot JSON), Origin/snapshot lifecycle, `origins` table — extended, Source config (OneDriveSourceConfig) — carried from spec 006, sync-only fields dropped, Source health (onedrive) (+14 more)

### Community 77 - "Port Alignment Quickstart"
Cohesion: 0.13
Nodes (13): Before → After, Contract: Port Alignment, Invariants, What does NOT change, Notes, Prerequisites, Quickstart: Port Alignment Validation, S1 — Sidecar aligned port (FR-001 / SC-001) (+5 more)

### Community 84 - "OneDrive Auth Contract"
Cohesion: 0.09
Nodes (22): Contract: OneDrive Source + `sources_auth` MCP Tools, Invariants, Request, Request, Response (already authenticated), Response (existing token, immediate sync), Response (no token, needs sign-in), Response (sign-in completed — checked after user returns) (+14 more)

### Community 91 - "Edge Case Tests"
Cohesion: 0.23
Nodes (6): call(), server(), test_budget_exhaustion_low_confidence(), test_concurrent_queries_consistent(), test_corrupt_and_encrypted_files_skipped_not_blocking(), test_laya_down_falls_back_and_reports()

### Community 92 - "form"
Cohesion: 0.04
Nodes (45): AccessibleIcon (radix `AccessibleIcon.Root`: `label` required), AspectRatio (radix `AspectRatio.Root`: `asChild`, `ratio` default `1`), avatar, Avatar.Fallback → Avatar.Fallback, Avatar.Image → Avatar.Image, Avatar.Root → Avatar.Root, Base UI only props worth knowing, Base UI only props worth knowing (+37 more)

### Community 93 - "form"
Cohesion: 0.04
Nodes (45): AccessibleIcon (radix `AccessibleIcon.Root`: `label` required), AspectRatio (radix `AspectRatio.Root`: `asChild`, `ratio` default `1`), avatar, Avatar.Fallback → Avatar.Fallback, Avatar.Image → Avatar.Image, Avatar.Root → Avatar.Root, Base UI only props worth knowing, Base UI only props worth knowing (+37 more)

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
Cohesion: 0.11
Nodes (19): Dependencies & Execution Order, Format: `[ID] [P?] [Story] Description`, Implementation for User Story 1, Implementation Strategy, Incremental Delivery, MVP First (User Story 1 Only), Notes, Parallel Example: User Story 1 (+11 more)

### Community 99 - "Research Extraction Tests"
Cohesion: 0.24
Nodes (6): extract_sections(), _html(), test_dirty_markup_noise_rules(), test_js_only_page_yields_no_sections_without_crashing(), test_ordered_page_sections_preserve_document_order(), test_oversized_page_truncated_at_bound_and_flagged()

### Community 100 - "page.tsx"
Cohesion: 0.08
Nodes (15): defaultStates, defaultStates, cannedReplies, Conversation, initialConversations, models, sidebarGroups, suggestions (+7 more)

### Community 102 - "select"
Cohesion: 0.05
Nodes (36): Base UI only props worth knowing (checkbox), Base UI only props worth knowing (radio-group), Base UI only props worth knowing (select), Base UI only props worth knowing (switch), checkbox, Checkbox.Indicator → Checkbox.Indicator, Checkbox.Root → Checkbox.Root, CSS variable mapping (select) (+28 more)

### Community 103 - "Button"
Cohesion: 0.13
Nodes (35): Step 5: Map Component Recipes to Variants, Assistant activity uses Trace, Message surfaces use Bubble, Buttons inside inputs use InputGroup + InputGroupAddon, Contents, Field validation and disabled states, FieldSet + FieldLegend for grouping related fields, Forms & Inputs (+27 more)

### Community 104 - "status"
Cohesion: 0.09
Nodes (23): Configuration surface, Contract: Logging Setup, Status Field & Error Handling, Error-response matrix (single source of truth), Test matrix (contract + unit + integration — every row is a named test), Tool: `status` (EXISTING — additive field), Complexity Tracking, Constitution Check, Documentation (this feature) (+15 more)

### Community 105 - "Per-component notes"
Cohesion: 0.08
Nodes (24): accordion, asChild -> render, breadcrumb / marker (Slot users), Coverage matrix, CSS custom properties, Data attributes / class hooks, dialog / alert-dialog / sheet, Doc-validation TODOs (before specs are final) (+16 more)

### Community 106 - "Feature Specification: Application Log File with Leveled Logging"
Cohesion: 0.10
Nodes (19): Content Quality, Feature Readiness, Notes, Requirement Completeness, Specification Quality Checklist: Application Log File with Leveled Logging, Assumptions, Clarifications, Edge Cases (+11 more)

### Community 107 - "Question Planner"
Cohesion: 0.36
Nodes (4): decompose(), test_planner_default_vector(), test_planner_multi_part(), test_planner_sql_keyword_routes_sql()

### Community 108 - "dropdown-menu.tsx"
Cohesion: 0.10
Nodes (17): Items always inside their Group component, Icons, Icons in Button use data-icon attribute, No sizing classes on icons inside components, Pass icons as component objects, not string keys, Items always inside their Group component, Icons, Icons in Button use data-icon attribute (+9 more)

### Community 109 - "SSRF Web Research"
Cohesion: 0.21
Nodes (5): _assert_public_host(), research_page(), research_pages(), sections_to_text(), _web_evidence()

### Community 110 - "Per-component notes"
Cohesion: 0.08
Nodes (24): accordion, asChild -> render, breadcrumb / marker (Slot users), Coverage matrix, CSS custom properties, Data attributes / class hooks, dialog / alert-dialog / sheet, Doc-validation TODOs (before specs are final) (+16 more)

### Community 111 - "Research Page Renderer"
Cohesion: 0.38
Nodes (4): render_page(), test_render_fallback_default_marker_when_no_snippet(), test_render_fallback_shows_snippet_with_visible_marker(), test_render_mirrors_grouped_structure_in_order()

### Community 112 - "Component Composition"
Cohesion: 0.12
Nodes (22): Avatar always needs AvatarFallback, Component Structure → [composition.md](./rules/composition.md), Avatar always needs AvatarFallback, Button has no isPending or isLoading prop, Callouts use Alert, Card structure, Choosing between overlay components, Component Composition (+14 more)

### Community 113 - "Separator"
Cohesion: 0.09
Nodes (23): System notes and dividers use Marker, Chat & Messaging → [chat.md](./rules/chat.md), CLI, Critical Rules, Icons → [icons.md](./rules/icons.md), Styling & Tailwind → [styling.md](./rules/styling.md), Use Components, Not Custom Markup → [composition.md](./rules/composition.md), Attachments use Attachment (+15 more)

### Community 114 - "Domain Filtering"
Cohesion: 0.33
Nodes (4): filter_by_domains(), test_filter_by_domains_empty_input(), test_filter_by_domains_no_matches(), test_filter_by_domains_substring_match()

### Community 115 - "Dify Specialty Agent"
Cohesion: 0.40
Nodes (4): Dify Chatflow with 13 MCP Tools, 13 MCP Tools, specialty_profiles MCP tool, specialty_search MCP tool

### Community 116 - "package.json"
Cohesion: 0.09
Nodes (21): eslintConfig, name, private, type, version, eslint, eslint-config-next, prettier (+13 more)

### Community 117 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 118 - "create_new_feature.py"
Cohesion: 0.20
Nodes (14): Args, _clean_branch_name(), _fit_branch_name(), _generate_branch_name(), _get_highest_from_specs(), _has_spec_prefix_conflict(), _help_text(), _int64_from_digits() (+6 more)

### Community 119 - "select"
Cohesion: 0.11
Nodes (19): Base UI only props worth knowing (select), CSS variable mapping (select), Data-attribute mapping (select), select, Select.Arrow → Select.Arrow, Select.Content → Select.Portal > Select.Positioner > Select.Popup (moved/split), Select.Group → Select.Group, Select.Icon → Select.Icon (+11 more)

### Community 120 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 122 - "Feature Documentation"
Cohesion: 0.50
Nodes (4): Documentation (this feature), Project Structure, Source Code (repository root), User-managed file (not committed to the repo)

### Community 123 - "Site-Scoped Query Builder"
Cohesion: 0.50
Nodes (3): construct_scoped_query(), test_construct_scoped_query_multiple_sites(), test_construct_scoped_query_single_site()

### Community 125 - "dropdown-menu (Radix `DropdownMenu` → Base UI `Menu`)"
Cohesion: 0.11
Nodes (18): Arrow → Menu.Arrow, Base UI only props worth knowing (Menu), CheckboxItem → Menu.CheckboxItem, CSS variable mapping (per menu flavor: `dropdown-menu` / `context-menu` / `menubar`), Data-attribute mapping (dropdown/context/menubar menus), dropdown-menu (Radix `DropdownMenu` → Base UI `Menu`), Group → Menu.Group, Item → Menu.Item (+10 more)

### Community 126 - "dropdown-menu (Radix `DropdownMenu` → Base UI `Menu`)"
Cohesion: 0.11
Nodes (18): Arrow → Menu.Arrow, Base UI only props worth knowing (Menu), CheckboxItem → Menu.CheckboxItem, CSS variable mapping (per menu flavor: `dropdown-menu` / `context-menu` / `menubar`), Data-attribute mapping (dropdown/context/menubar menus), dropdown-menu (Radix `DropdownMenu` → Base UI `Menu`), Group → Menu.Group, Item → Menu.Item (+10 more)

### Community 127 - "logging_setup.py"
Cohesion: 0.14
Nodes (8): D5: Redaction filter + DEBUG-only discipline at call sites, D6: Rotation + startup writability probe, D7: `status` additive field from a module-level `LoggingSetup`, Phase 2: Foundational (Blocking Prerequisites), configure_logging(), current_setup(), LoggingSetup, RedactionFilter

### Community 128 - "loop"
Cohesion: 0.12
Nodes (16): Callback signature rule, Consumer-side prop changes (call sites, not wrappers), Per component, Sweep procedure, Universal, Content → Menu.Portal > Menu.Positioner > Menu.Popup, Data attributes / CSS variables, Menu → Menu.Root (+8 more)

### Community 129 - "layout.tsx"
Cohesion: 0.15
Nodes (13): Slider.Thumb → Slider.Thumb, Slider.Thumb → Slider.Thumb, fontMono, inter, metadata, RootLayout(), isTypingTarget(), ThemeHotkey() (+5 more)

### Community 130 - "agent/skills/shadcn/scripts/showcase-coverage.mjs"
Cohesion: 0.13
Nodes (12): components, missing, source, [uiArg, ...roots], uiDir, walk(), components, missing (+4 more)

### Community 131 - "json"
Cohesion: 0.23
Nodes (7): resolve_template_content(), compose_from_base(), TemplateResolutionError, main(), _help_text(), _json_line(), main()

### Community 132 - "check_prerequisites.py"
Cohesion: 0.28
Nodes (12): Args, _available_docs(), _check_dir(), _check_file(), _dir_has_entries(), _json_line(), main(), _parse_args() (+4 more)

### Community 133 - "context-menu (Radix `ContextMenu` → Base UI `ContextMenu`)"
Cohesion: 0.13
Nodes (14): Arrow / Item / Group / Label / CheckboxItem / RadioGroup / RadioItem / ItemIndicator / Separator / Sub / SubTrigger / SubContent, Base UI only, data attributes, CSS variables, Content → ContextMenu.Portal > Positioner > Popup, context-menu (Radix `ContextMenu` → Base UI `ContextMenu`), Data attributes / CSS variables, Menu → Menu.Root, menubar (Radix `Menubar` → Base UI `Menubar` + `Menu`), Portal / Content / Arrow / Item / Group / Label / CheckboxItem / RadioGroup / RadioItem / ItemIndicator / Separator / Sub / SubTrigger / SubContent (+6 more)

### Community 134 - "navigation-menu (Radix `NavigationMenu` → Base UI `NavigationMenu`)"
Cohesion: 0.14
Nodes (14): Base UI only props worth knowing (NavigationMenu), Content → NavigationMenu.Content, CSS variable mapping (navigation-menu), Data-attribute mapping (navigation-menu), Gaps / caveats, Indicator → NavigationMenu.Icon (per wrapper ground truth), Item → NavigationMenu.Item, Link → NavigationMenu.Link (+6 more)

### Community 135 - "Customization & Theming"
Cohesion: 0.14
Nodes (14): 1. Built-in variants, 2. Tailwind classes via `className`, 3. Add a new variant, 4. Wrapper components, Adding Custom Colors, Border Radius, Changing the Theme, Checking for Updates (+6 more)

### Community 136 - "navigation-menu (Radix `NavigationMenu` → Base UI `NavigationMenu`)"
Cohesion: 0.14
Nodes (14): Base UI only props worth knowing (NavigationMenu), Content → NavigationMenu.Content, CSS variable mapping (navigation-menu), Data-attribute mapping (navigation-menu), Gaps / caveats, Indicator → NavigationMenu.Icon (per wrapper ground truth), Item → NavigationMenu.Item, Link → NavigationMenu.Link (+6 more)

### Community 137 - "Customization & Theming"
Cohesion: 0.14
Nodes (14): 1. Built-in variants, 2. Tailwind classes via `className`, 3. Add a new variant, 4. Wrapper components, Adding Custom Colors, Border Radius, Changing the Theme, Checking for Updates (+6 more)

### Community 138 - "dependencies"
Cohesion: 0.14
Nodes (14): dependencies, @base-ui/react, class-variance-authority, cn, lucide-react, next, next-themes, react (+6 more)

### Community 139 - "agent/skills/migrate-radix-to-base/disclosure.md"
Cohesion: 0.15
Nodes (12): Base UI only props worth knowing, Base UI only props worth knowing, CSS var mapping, CSS var mapping, Data-attribute mapping, Data-attribute mapping, Radix → Base UI props mapping: disclosure + toggle family, toggle (+4 more)

### Community 140 - "The Design System Page"
Cohesion: 0.15
Nodes (13): Block anatomy, Checklist, Components: Tiers and Block Anatomy, Contents, Do and Don't, Edge Cases, Helpers, Page Outline (+5 more)

### Community 141 - "Styling & Customization"
Cohesion: 0.15
Nodes (13): Built-in variants first, className for layout only, Contents, No manual dark: color overrides, No manual z-index on overlay components, No raw color values for status/state indicators, No space-x-* / space-y-*, Prefer size-* over w-* h-* when equal (+5 more)

### Community 142 - "The Design System Page"
Cohesion: 0.15
Nodes (13): Block anatomy, Checklist, Components: Tiers and Block Anatomy, Contents, Do and Don't, Edge Cases, Helpers, Page Outline (+5 more)

### Community 143 - "Styling & Customization"
Cohesion: 0.15
Nodes (13): Built-in variants first, className for layout only, Contents, No manual dark: color overrides, No manual z-index on overlay components, No raw color values for status/state indicators, No space-x-* / space-y-*, Prefer size-* over w-* h-* when equal (+5 more)

### Community 144 - "alert-dialog"
Cohesion: 0.17
Nodes (12): Action → (no primitive), alert-dialog, Base UI only props worth knowing (alert-dialog), Cancel → Close, Content → Popup, CSS variables (alert-dialog), Data attributes (alert-dialog), Overlay → Backdrop (+4 more)

### Community 145 - "agent/skills/shadcn/assets/showcase/color-pair.tsx"
Cohesion: 0.27
Nodes (10): ColorPair(), contrast(), luminance(), toHex(), toRgb(), ColorPair(), contrast(), luminance() (+2 more)

### Community 146 - "Design Systems from DESIGN.md"
Cohesion: 0.17
Nodes (12): Contents, Coverage check, Design Systems from DESIGN.md, Inputs to Confirm, Known traps, Picking a style, Report Back, Step 1: Scaffold (+4 more)

### Community 147 - "Tools"
Cohesion: 0.17
Nodes (11): Configuring Registries, Setup, `shadcn:get_add_command_for_items`, `shadcn:get_audit_checklist`, `shadcn:get_item_examples_from_registries`, `shadcn:get_project_registries`, `shadcn:list_items_in_registries`, shadcn MCP Server (+3 more)

### Community 148 - ".agents/skills/migrate-radix-to-base/form-controls.md"
Cohesion: 0.17
Nodes (11): Base UI only props worth knowing (checkbox), Base UI only props worth knowing (switch), checkbox, Checkbox.Indicator → Checkbox.Indicator, Checkbox.Root → Checkbox.Root, Data-attribute mapping (checkbox), Data-attribute mapping (switch), Radix UI to Base UI props mapping: form controls (+3 more)

### Community 149 - "alert-dialog"
Cohesion: 0.17
Nodes (12): Action → (no primitive), alert-dialog, Base UI only props worth knowing (alert-dialog), Cancel → Close, Content → Popup, CSS variables (alert-dialog), Data attributes (alert-dialog), Overlay → Backdrop (+4 more)

### Community 150 - "Design Systems from DESIGN.md"
Cohesion: 0.17
Nodes (12): Contents, Coverage check, Design Systems from DESIGN.md, Inputs to Confirm, Known traps, Picking a style, Report Back, Step 1: Scaffold (+4 more)

### Community 151 - "Tools"
Cohesion: 0.17
Nodes (11): Configuring Registries, Setup, `shadcn:get_add_command_for_items`, `shadcn:get_audit_checklist`, `shadcn:get_item_examples_from_registries`, `shadcn:get_project_registries`, `shadcn:list_items_in_registries`, shadcn MCP Server (+3 more)

### Community 152 - "setup_tasks.py"
Cohesion: 0.33
Nodes (8): _available_docs(), _check_dir(), _check_file(), _dir_has_entries(), _help_text(), _json_line(), main(), _status_marker()

### Community 153 - "toast"
Cohesion: 0.18
Nodes (11): Base UI only props worth knowing, CSS variables, Data attributes, toast, Toast.Action → Toast.Action, Toast.Close → Toast.Close, Toast.Description → Toast.Description, Toast.Provider → Toast.Provider (+3 more)

### Community 154 - "popover"
Cohesion: 0.18
Nodes (11): Anchor → Positioner `anchor` prop, Arrow → Arrow, Base UI only props worth knowing (popover), Close → Close, Content → Positioner + Popup, CSS variables (popover), Data attributes (popover), popover (+3 more)

### Community 156 - "Page"
Cohesion: 0.27
Nodes (9): Composition: asChild (radix) vs render (base), Composition: asChild (radix) vs render (base), Page(), demoStream(), send(), updateConversation(), updateMessage(), parseAnswer() (+1 more)

### Community 157 - "Component Composition"
Cohesion: 0.18
Nodes (11): Button has no isPending or isLoading prop, Callouts use Alert, Card structure, Choosing between overlay components, Component Composition, Contents, Dialog, Sheet, and Drawer always need a Title, Empty states use Empty component (+3 more)

### Community 158 - "popover"
Cohesion: 0.18
Nodes (11): Anchor → Positioner `anchor` prop, Arrow → Arrow, Base UI only props worth knowing (popover), Close → Close, Content → Positioner + Popup, CSS variables (popover), Data attributes (popover), popover (+3 more)

### Community 160 - "markdown.tsx"
Cohesion: 0.40
Nodes (7): Markdown(), Table(), TableBody(), TableCell(), TableHead(), TableHeader(), TableRow()

### Community 161 - "devDependencies"
Cohesion: 0.18
Nodes (11): devDependencies, eslint, eslint-config-next, prettier, prettier-plugin-tailwindcss, tailwindcss, @tailwindcss/postcss, @types/node (+3 more)

### Community 162 - "Quickstart: OneDrive On-Demand Embedding with Staleness Reminder"
Cohesion: 0.20
Nodes (6): 1. Automated validation (CI-grade, no network), 2. Live on-demand flow (real OneDrive), 3. Chat-level check (Dify), Expected outcomes summary, Prerequisites, Quickstart: OneDrive On-Demand Embedding with Staleness Reminder

### Community 163 - "toolbar"
Cohesion: 0.20
Nodes (10): Base UI only props worth knowing, CSS var mapping, Data-attribute mapping, toolbar, Toolbar.Button → Toolbar.Button, Toolbar.Link → Toolbar.Link, Toolbar.Root → Toolbar.Root, Toolbar.Separator → Toolbar.Separator (+2 more)

### Community 164 - "tooltip"
Cohesion: 0.20
Nodes (10): Arrow → Arrow, Base UI only props worth knowing (tooltip), Content → Positioner + Popup, CSS variables (tooltip), Data attributes (tooltip), Portal → Portal, Provider → Provider, Root → Root (+2 more)

### Community 165 - "dialog"
Cohesion: 0.20
Nodes (10): Base UI only props worth knowing (dialog), Content → Popup, CSS variables (dialog), Data attributes (dialog), dialog, Overlay → Backdrop, Portal → Portal, Root → Root (+2 more)

### Community 166 - "Target wrapper shapes (golden-derived specifics)"
Cohesion: 0.20
Nodes (9): Accordion animation placement, Button, Conventions, DropdownMenu / ContextMenu SubContent, Select, SubTrigger open styling, Tabs, Target wrapper shapes (golden-derived specifics) (+1 more)

### Community 167 - "add"
Cohesion: 0.24
Nodes (10): `add` — Add components, Dry-Run Mode, Smart Merge from Upstream, Workflow, Toast.Root → Toast.Root, `add` — Add components, Dry-Run Mode, Smart Merge from Upstream (+2 more)

### Community 168 - "toast"
Cohesion: 0.20
Nodes (10): Base UI only props worth knowing, CSS variables, Data attributes, toast, Toast.Action → Toast.Action, Toast.Close → Toast.Close, Toast.Description → Toast.Description, Toast.Provider → Toast.Provider (+2 more)

### Community 169 - "tooltip"
Cohesion: 0.20
Nodes (10): Arrow → Arrow, Base UI only props worth knowing (tooltip), Content → Positioner + Popup, CSS variables (tooltip), Data attributes (tooltip), Portal → Portal, Provider → Provider, Root → Root (+2 more)

### Community 170 - "dialog"
Cohesion: 0.20
Nodes (10): Base UI only props worth knowing (dialog), Content → Popup, CSS variables (dialog), Data attributes (dialog), dialog, Overlay → Backdrop, Portal → Portal, Root → Root (+2 more)

### Community 171 - "Target wrapper shapes (golden-derived specifics)"
Cohesion: 0.20
Nodes (9): Accordion animation placement, Button, Conventions, DropdownMenu / ContextMenu SubContent, Select, SubTrigger open styling, Tabs, Target wrapper shapes (golden-derived specifics) (+1 more)

### Community 173 - "accordion"
Cohesion: 0.22
Nodes (9): accordion, Accordion.Content → Accordion.Panel, Accordion.Header → Accordion.Header, Accordion.Item → Accordion.Item, Accordion.Root → Accordion.Root, Accordion.Trigger → Accordion.Trigger, Base UI only props worth knowing, CSS var mapping (+1 more)

### Community 174 - "context-menu (Radix `ContextMenu` → Base UI `ContextMenu`)"
Cohesion: 0.22
Nodes (8): Arrow / Item / Group / Label / CheckboxItem / RadioGroup / RadioItem / ItemIndicator / Separator / Sub / SubTrigger / SubContent, Base UI only, data attributes, CSS variables, Content → ContextMenu.Portal > Positioner > Popup, context-menu (Radix `ContextMenu` → Base UI `ContextMenu`), Portal → ContextMenu.Portal, Radix → Base UI props mapping: menu family, Root → ContextMenu.Root, Trigger → ContextMenu.Trigger

### Community 175 - "hover-card → preview-card"
Cohesion: 0.22
Nodes (9): Arrow → Arrow, Base UI only props worth knowing (preview-card), Content → Positioner + Popup, CSS variables (preview-card), Data attributes (preview-card), hover-card → preview-card, Portal → Portal, Root → Root (+1 more)

### Community 176 - "Commands"
Cohesion: 0.22
Nodes (9): `apply` — Apply a preset to an existing project, `build` — Build a custom registry, Commands, `diff` — Check for updates, `docs` — Get component documentation URLs, `info` — Project information, `init` — Initialize or create a project, `search` — Search registries (+1 more)

### Community 177 - "hover-card → preview-card"
Cohesion: 0.22
Nodes (9): Arrow → Arrow, Base UI only props worth knowing (preview-card), Content → Positioner + Popup, CSS variables (preview-card), Data attributes (preview-card), hover-card → preview-card, Portal → Portal, Root → Root (+1 more)

### Community 178 - "Commands"
Cohesion: 0.22
Nodes (9): `apply` — Apply a preset to an existing project, `build` — Build a custom registry, Commands, `diff` — Check for updates, `docs` — Get component documentation URLs, `info` — Project information, `init` — Initialize or create a project, `search` — Search registries (+1 more)

### Community 179 - "tabs"
Cohesion: 0.25
Nodes (8): Base UI only props worth knowing, CSS var mapping, Data-attribute mapping, tabs, Tabs.Content → Tabs.Panel, Tabs.List → Tabs.List, Tabs.Root → Tabs.Root, Tabs.Trigger → Tabs.Tab

### Community 180 - "Step 4: Map Tokens to the Theme"
Cohesion: 0.25
Nodes (8): Dark mode, Elevation, Focus, Fonts, Radius, Role mapping, Step 4: Map Tokens to the Theme, Type scale

### Community 181 - "Foundations"
Cohesion: 0.25
Nodes (8): Color roles, Elevation, Foundations, Motion and icons, Palette, Radius, Spacing, Typography

### Community 182 - "Registry Authoring and Addresses"
Cohesion: 0.25
Nodes (8): Address Schemes, Build and Verify, GitHub Registries, Include, Mental Model, Registry Authoring and Addresses, Registry Dependencies, Root `registry.json`

### Community 183 - "Base vs Radix"
Cohesion: 0.25
Nodes (8): Accordion, Base vs Radix, Button / trigger as non-button element (base only), Contents, Select, Select — multiple selection and object values (base only), Slider, ToggleGroup

### Community 184 - "Chat & Messaging"
Cohesion: 0.25
Nodes (8): Attachments use Attachment, Chat & Messaging, Code and tool output use CodeBlock, Contents, Escape hatch: the scroller hooks, Message rows use Message, Scrollable threads use MessageScroller, Streaming, anchoring, and jump-to-latest are built in

### Community 185 - "Step 4: Map Tokens to the Theme"
Cohesion: 0.25
Nodes (8): Dark mode, Elevation, Focus, Fonts, Radius, Role mapping, Step 4: Map Tokens to the Theme, Type scale

### Community 186 - "Foundations"
Cohesion: 0.25
Nodes (8): Color roles, Elevation, Foundations, Motion and icons, Palette, Radius, Spacing, Typography

### Community 187 - "Registry Authoring and Addresses"
Cohesion: 0.25
Nodes (8): Address Schemes, Build and Verify, GitHub Registries, Include, Mental Model, Registry Authoring and Addresses, Registry Dependencies, Root `registry.json`

### Community 188 - "Base vs Radix"
Cohesion: 0.25
Nodes (8): Accordion, Base vs Radix, Button / trigger as non-button element (base only), Contents, Select, Select — multiple selection and object values (base only), Slider, ToggleGroup

### Community 189 - "Quickstart: OneDrive Ingestion Validation"
Cohesion: 0.25
Nodes (8): Notes, Prerequisites, Quickstart: OneDrive Ingestion Validation, S1 — Add a OneDrive source (FR-001), S2 — Complete device sign-in (FR-003), S3 — Verify files are searchable (SC-001), S4 — Auto-update (SC-002/003), S5 — Auth expiry (SC-004)

### Community 190 - "heuristic_classify"
Cohesion: 0.36
Nodes (4): heuristic_classify(), test_default_is_deliberative(), test_multi_part_question_deliberative(), test_simple_question_fast()

### Community 191 - "Class-string rewrites (layer 2)"
Cohesion: 0.29
Nodes (6): Animation idiom, Class-string rewrites (layer 2), CSS variables, Data-attribute selectors, Disabled-state hooks, Element changes kill pseudo-class variants

### Community 192 - "collapsible"
Cohesion: 0.29
Nodes (7): Base UI only props worth knowing, collapsible, Collapsible.Content → Collapsible.Panel, Collapsible.Root → Collapsible.Root, Collapsible.Trigger → Collapsible.Trigger, CSS var mapping, Data-attribute mapping

### Community 193 - "slider"
Cohesion: 0.29
Nodes (7): Base UI only props worth knowing (slider), Data-attribute mapping (slider), (new part) Slider.Control, slider, Slider.Range → Slider.Indicator (renamed), Slider.Root → Slider.Root, Slider.Track → Slider.Track (moved inside Control)

### Community 194 - "Radix UI -> Base UI migration"
Cohesion: 0.29
Nodes (6): Hard rules, Modes, Preflight (always), Radix UI -> Base UI migration, Strategy: golden pair first, transformation engine second, Verify and report

### Community 195 - "Class-string rewrites (layer 2)"
Cohesion: 0.29
Nodes (6): Animation idiom, Class-string rewrites (layer 2), CSS variables, Data-attribute selectors, Disabled-state hooks, Element changes kill pseudo-class variants

### Community 196 - "slider"
Cohesion: 0.29
Nodes (7): Base UI only props worth knowing (slider), Data-attribute mapping (slider), (new part) Slider.Control, slider, Slider.Range → Slider.Indicator (renamed), Slider.Root → Slider.Root, Slider.Track → Slider.Track (moved inside Control)

### Community 197 - "Radix UI -> Base UI migration"
Cohesion: 0.29
Nodes (6): Hard rules, Modes, Preflight (always), Radix UI -> Base UI migration, Strategy: golden pair first, transformation engine second, Verify and report

### Community 198 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, start, typecheck

### Community 199 - "Consumer-side prop changes (call sites, not wrappers)"
Cohesion: 0.33
Nodes (5): Callback signature rule, Consumer-side prop changes (call sites, not wrappers), Per component, Sweep procedure, Universal

### Community 200 - "radio-group"
Cohesion: 0.33
Nodes (6): Base UI only props worth knowing (radio-group), Data-attribute mapping (radio-group), radio-group, RadioGroup.Indicator → Radio.Indicator (moved to Radio namespace), RadioGroup.Item → Radio.Root (moved to Radio namespace), RadioGroup.Root → RadioGroup

### Community 202 - "shadcn CLI Reference"
Cohesion: 0.40
Nodes (5): Contents, Presets, shadcn CLI Reference, Switching Presets, Templates

### Community 203 - "shadcn CLI Reference"
Cohesion: 0.40
Nodes (5): Contents, Presets, shadcn CLI Reference, Switching Presets, Templates

### Community 205 - "Next.js template"
Cohesion: 0.50
Nodes (3): Adding components, Next.js template, Using components

### Community 206 - "Dependencies & Execution Order"
Cohesion: 0.50
Nodes (4): Dependencies & Execution Order, Parallel Opportunities, Phase Dependencies, Within Each User Story

## Knowledge Gaps
- **65 isolated node(s):** `react-dom`, `shadcn`, `tw-animate-css`, `@tailwindcss/postcss`, `@types/node` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1572 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `build_server()` connect `Logging Design Decisions` to `Reflexion Graph Agent`, `OneDrive Freshness Probe`, `Vector Store Wrapper`, `Specialty Web Search`, `OneDrive Contract Tests`, `Logging and Tool Models`, `State Store Methods`, `OneDrive On-Demand Tests`, `Web Search Providers`, `Logging Integration Tests`, `Server Transport Config`, `OneDrive Graph Auth`, `Specialty Search Integration`, `Fallback Provenance Tests`, `Web Research Integration`, `Laya Runtime`, `Specialty Search Contract`, `MCP Server Core`, `Web Research Contract`, `Reflexion Quickstart Tests`, `Decision Routing Tests`, `sources_auth`, `MCP Contract Tests`, `Logging Contract Tests`, `OneDrive On-Demand Tools`, `Success Criteria Tests`, `Ask Response Contract`, `SQLite State Tools`, `shadcn/ui`, `Web Search Scrape Tasks`, `OneDrive Auth Contract`, `Edge Case Tests`, `Specialty Search Plan`, `Provider Chain Tests`, `status`, `SSRF Web Research`, `Research Page Renderer`, `Domain Filtering`, `Site-Scoped Query Builder`, `logging_setup.py`?**
  _High betweenness centrality (0.274) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `build_server()` (e.g. with `D7: Migration — snapshot-absence defines the pending set; idempotent by construction` and `Phase 8: Cross-Cutting — One-Time Migration (FR-016)`) actually correct?**
  _`build_server()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `shadcn`, `tw-animate-css` to the rest of the system?**
  _65 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `rl_common.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05023796932839767 - nodes in this community are weakly interconnected._
- **Why does `status()` connect `status` to `Quickstart: OneDrive On-Demand Embedding with Staleness Reminder`, `Logging Task Plan`, `Button`, `Feature Specification: Application Log File with Leveled Logging`, `Data Model: OneDrive On-Demand Embedding with Staleness Reminder`, `Logging Design Decisions`, `OneDrive Auth Contract`, `Server Transport Config`, `logging_setup.py`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `ProviderError` (e.g. with `Error taxonomy (binding mapping)` and `D9: Error handling — one honest per-file outcome model everywhere`) actually correct?**
  _`ProviderError` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Should `Dual-System Workflow Contracts` be split into smaller, more focused modules?**
  _Cohesion score 0.06612021857923497 - nodes in this community are weakly interconnected._