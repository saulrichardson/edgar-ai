Prompt-Builder enrichment
*   Include each field's name, JSON-type, description and "required" flag in the generated system prompt.
*   Provide a unit test to assert the prompt contains all field names.
Snapshot side-car metadata
• Nhen saving a prompt files create aurompt> meta son holding
{ "schema_hash":
"goal_overview":
"model": "gpt-40-mini" }.
• When saving rows: append a placeholder critic_score field to each row dict (will be populated in Phase 5).
Tests
• tests/unit/test_prompt_builder.py - simulate mode,
small
schema - prompt contains field list.
*   tests/unit/test_extractor.py - feed tool call missing optional field - row gets None without raising.
*   tests/integration/test_extract.py - run CLI in simulate mode and assert at least one JSON row whose keys equal the schema properties.
Settings additions
• prompt_builder_max_tokens, extractor max_retries, extractor_validation (default True) in config-py.
Documentation updates
• README + docs/architecture.md: new prompt structure and extractor validation logic.
Once these are implemented Phase 4 will be fully complete and the pipeline will be ready for the Critic → Governor feedback loop in Phase 5.
