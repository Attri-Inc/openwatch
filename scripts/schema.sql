CREATE TABLE cowork__api_keys (
  key_id TEXT NOT NULL,
  key_hash TEXT NOT NULL,
  aes_key_hex TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  organization_uuid TEXT,
  created_at TEXT,
  last_used_at TEXT,
  revoked INTEGER
);
CREATE TABLE cowork__audit_events (
  id INTEGER NOT NULL,
  worker_id TEXT,
  session_id TEXT,
  type TEXT NOT NULL,
  subtype TEXT,
  uuid TEXT,
  timestamp TEXT,
  content_preview TEXT,
  rate_limit_info TEXT,
  raw_json TEXT,
  source_file TEXT NOT NULL,
  byte_offset INTEGER NOT NULL,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__audit_permissions (
  id INTEGER NOT NULL,
  audit_event_id INTEGER,
  worker_id TEXT,
  session_id TEXT,
  timestamp TEXT,
  event_subtype TEXT,
  tool_name TEXT,
  tool_input TEXT,
  decision TEXT,
  granted INTEGER,
  source_file TEXT,
  byte_offset INTEGER,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__audit_result_success (
  id INTEGER NOT NULL,
  audit_event_id INTEGER,
  worker_id TEXT,
  session_id TEXT,
  timestamp TEXT,
  duration_ms INTEGER,
  duration_api_ms INTEGER,
  num_turns INTEGER,
  total_cost_usd REAL,
  model_usage_json TEXT,
  permission_denials TEXT,
  fast_mode_state TEXT,
  stop_reason TEXT,
  is_error INTEGER,
  result_text TEXT,
  source_file TEXT,
  byte_offset INTEGER,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__audit_system_init (
  id INTEGER NOT NULL,
  audit_event_id INTEGER,
  worker_id TEXT,
  session_id TEXT,
  timestamp TEXT,
  claude_code_version TEXT,
  agents_json TEXT,
  mcp_servers_json TEXT,
  plugins_json TEXT,
  skills_json TEXT,
  tools_json TEXT,
  model TEXT,
  permission_mode TEXT,
  output_style TEXT,
  source_file TEXT,
  byte_offset INTEGER,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__audit_tool_use_summary (
  id INTEGER NOT NULL,
  audit_event_id INTEGER,
  worker_id TEXT,
  session_id TEXT,
  timestamp TEXT,
  summary_text TEXT,
  preceding_tool_use_ids TEXT,
  source_file TEXT,
  byte_offset INTEGER,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__cowork_settings (
  account_uuid TEXT NOT NULL,
  organization_uuid TEXT,
  settings_json TEXT,
  first_start_time TEXT,
  migration_flags TEXT,
  ingested_at TEXT
);
CREATE TABLE cowork__documents (
  doc_id INTEGER NOT NULL,
  worker_id TEXT,
  account_uuid TEXT,
  direction TEXT NOT NULL,
  filename TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size INTEGER,
  discovered_at TEXT
);
CREATE TABLE cowork__file_offsets (
  file_path TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  byte_offset INTEGER NOT NULL,
  last_modified REAL,
  updated_at TEXT
);
CREATE TABLE cowork__machines (
  machine_id TEXT NOT NULL,
  hostname TEXT,
  os TEXT,
  first_seen_at TEXT,
  last_seen_at TEXT
);
CREATE TABLE cowork__messages (
  uuid TEXT NOT NULL,
  session_id TEXT NOT NULL,
  worker_id TEXT,
  parent_uuid TEXT,
  type TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  model TEXT,
  stop_reason TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cache_creation_tokens INTEGER,
  cache_read_tokens INTEGER,
  cost_usd REAL,
  content_text TEXT,
  has_thinking INTEGER,
  version TEXT,
  git_branch TEXT,
  is_sidechain INTEGER,
  user_type TEXT,
  cwd TEXT,
  permission_mode TEXT,
  request_id TEXT,
  server_tool_use TEXT,
  service_tier TEXT,
  speed TEXT,
  source_file TEXT NOT NULL,
  byte_offset INTEGER NOT NULL,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__organizations (
  organization_uuid TEXT NOT NULL,
  name TEXT,
  created_at TEXT
);
CREATE TABLE cowork__plugins (
  plugin_id TEXT NOT NULL,
  account_uuid TEXT NOT NULL,
  organization_uuid TEXT,
  source TEXT NOT NULL,
  name TEXT,
  install_path TEXT,
  version TEXT,
  marketplace_id TEXT,
  marketplace_name TEXT,
  git_commit_sha TEXT,
  installed_at TEXT,
  updated_at TEXT,
  raw_json TEXT,
  ingested_at TEXT
);
CREATE TABLE cowork__queue_operations (
  id INTEGER NOT NULL,
  session_id TEXT NOT NULL,
  worker_id TEXT,
  operation TEXT NOT NULL,
  timestamp TEXT,
  content TEXT,
  source_file TEXT NOT NULL,
  byte_offset INTEGER NOT NULL,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__scheduled_tasks (
  task_id TEXT NOT NULL,
  account_uuid TEXT,
  organization_uuid TEXT,
  cron_expression TEXT,
  enabled INTEGER,
  file_path TEXT,
  disable_jitter INTEGER,
  last_run_at TEXT,
  created_at INTEGER,
  raw_json TEXT,
  ingested_at TEXT
);
CREATE TABLE cowork__schema_version (
  version INTEGER NOT NULL,
  applied_at TEXT
);
CREATE TABLE cowork__sessions (
  session_id TEXT NOT NULL,
  worker_id TEXT,
  account_uuid TEXT,
  project_hash TEXT,
  first_timestamp TEXT,
  last_timestamp TEXT,
  user_message_count INTEGER,
  assistant_message_count INTEGER,
  total_input_tokens INTEGER,
  total_output_tokens INTEGER,
  total_cache_creation_tokens INTEGER,
  total_cache_read_tokens INTEGER,
  total_cost_usd REAL,
  actual_cost_usd REAL,
  primary_model TEXT
);
CREATE TABLE cowork__skills (
  skill_id TEXT NOT NULL,
  organization_uuid TEXT,
  account_uuid TEXT,
  name TEXT,
  description TEXT,
  creator_type TEXT,
  enabled INTEGER,
  updated_at TEXT,
  raw_json TEXT,
  ingested_at TEXT
);
CREATE TABLE cowork__spaces (
  space_id TEXT NOT NULL,
  account_uuid TEXT,
  organization_uuid TEXT,
  name TEXT,
  folders TEXT,
  projects TEXT,
  links TEXT,
  created_at INTEGER,
  updated_at INTEGER,
  raw_json TEXT,
  ingested_at TEXT
);
CREATE TABLE cowork__system_events (
  id INTEGER NOT NULL,
  session_id TEXT NOT NULL,
  worker_id TEXT,
  subtype TEXT,
  cwd TEXT,
  tools TEXT,
  source_file TEXT NOT NULL,
  byte_offset INTEGER NOT NULL,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__tool_calls (
  tool_use_id TEXT NOT NULL,
  message_uuid TEXT,
  session_id TEXT NOT NULL,
  worker_id TEXT,
  tool_name TEXT NOT NULL,
  tool_category TEXT,
  tool_input TEXT,
  timestamp TEXT,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__tool_results (
  tool_use_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  result_text TEXT,
  is_error INTEGER,
  ingested_at TEXT,
  account_uuid TEXT
);
CREATE TABLE cowork__user_reports (
  id INTEGER NOT NULL,
  email TEXT NOT NULL,
  month TEXT NOT NULL,
  report_type TEXT NOT NULL,
  content TEXT NOT NULL,
  model_used TEXT,
  total_cost_usd REAL,
  created_at TEXT
);
CREATE TABLE cowork__users (
  account_uuid TEXT NOT NULL,
  email TEXT,
  organization_uuid TEXT,
  display_name TEXT,
  machine_id TEXT,
  raw_json TEXT,
  ingested_at TEXT
);
CREATE TABLE cowork__worker_feature_flags (
  worker_id TEXT NOT NULL,
  feature_name TEXT NOT NULL,
  feature_value TEXT,
  ingested_at TEXT
);
CREATE TABLE cowork__worker_tool_usage (
  id INTEGER NOT NULL,
  worker_id TEXT NOT NULL,
  item_type TEXT NOT NULL,
  item_name TEXT NOT NULL,
  use_count INTEGER,
  last_used_at INTEGER,
  ingested_at TEXT
);
CREATE TABLE cowork__workers (
  worker_id TEXT NOT NULL,
  account_uuid TEXT,
  organization_uuid TEXT,
  session_name TEXT,
  cli_session_id TEXT,
  title TEXT,
  model TEXT,
  cwd TEXT,
  session_type TEXT,
  initial_message TEXT,
  system_prompt TEXT,
  project_folders TEXT,
  slash_commands TEXT,
  remote_mcp_config TEXT,
  enabled_mcp_tools TEXT,
  egress_allowed_domains TEXT,
  user_approved_paths TEXT,
  file_delete_approved TEXT,
  fs_detected_files TEXT,
  scheduled_task_id TEXT,
  space_id TEXT,
  account_name TEXT,
  email_address TEXT,
  memory_enabled INTEGER,
  host_loop_mode INTEGER,
  is_archived INTEGER,
  created_at INTEGER,
  last_activity_at INTEGER,
  mcq_answers TEXT,
  origin_cwd TEXT,
  worktree_name TEXT,
  worktree_path TEXT,
  permission_mode TEXT,
  metadata_json TEXT,
  machine_id TEXT,
  ingested_at TEXT
);
CREATE TABLE compliance__claude_activities (
  id INTEGER NOT NULL,
  activity_id TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  actor_type TEXT,
  actor_user_id TEXT,
  actor_email TEXT,
  actor_ip TEXT,
  actor_user_agent TEXT,
  actor_api_key_id TEXT,
  organization_id INTEGER,
  request_id TEXT,
  request_method TEXT,
  request_url TEXT,
  status_code INTEGER,
  organization_uuid TEXT,
  claude_chat_id TEXT,
  claude_project_id TEXT,
  claude_file_id TEXT,
  filename TEXT,
  raw_response TEXT,
  source_created_at TEXT NOT NULL,
  created_at TEXT,
  claude_artifact_id TEXT,
  preview_only INTEGER,
  request_body TEXT
);
CREATE TABLE compliance__claude_artifacts (
  id INTEGER NOT NULL,
  claude_artifact_id TEXT,
  version_id TEXT NOT NULL,
  message_id INTEGER,
  title TEXT,
  artifact_type TEXT,
  content TEXT,
  content_synced INTEGER,
  synced_at TEXT,
  created_at TEXT
);
CREATE TABLE compliance__claude_chat_messages (
  id INTEGER NOT NULL,
  claude_message_id TEXT NOT NULL,
  chat_id INTEGER,
  role TEXT NOT NULL,
  content TEXT,
  content_blocks TEXT,
  files TEXT,
  artifacts TEXT,
  source_created_at TEXT,
  created_at TEXT
);
CREATE TABLE compliance__claude_chats (
  id INTEGER NOT NULL,
  claude_chat_id TEXT NOT NULL,
  name TEXT,
  organization_id INTEGER,
  project_id INTEGER,
  user_id INTEGER,
  source_created_at TEXT,
  source_updated_at TEXT,
  deleted_at TEXT,
  messages_synced INTEGER,
  raw_response TEXT,
  synced_at TEXT,
  created_at TEXT
);
CREATE TABLE compliance__claude_organizations (
  id INTEGER NOT NULL,
  uuid TEXT NOT NULL,
  name TEXT NOT NULL,
  source_created_at TEXT,
  raw_response TEXT,
  synced_at TEXT,
  created_at TEXT,
  org_id TEXT
);
CREATE TABLE compliance__claude_project_attachments (
  id INTEGER NOT NULL,
  claude_attachment_id TEXT NOT NULL,
  project_id INTEGER,
  attachment_type TEXT,
  filename TEXT,
  mime_type TEXT,
  source_created_at TEXT,
  raw_response TEXT,
  synced_at TEXT,
  created_at TEXT
);
CREATE TABLE compliance__claude_projects (
  id INTEGER NOT NULL,
  claude_project_id TEXT NOT NULL,
  name TEXT,
  description TEXT,
  instructions TEXT,
  is_private INTEGER,
  organization_id INTEGER,
  user_id INTEGER,
  chats_count INTEGER,
  attachments_count INTEGER,
  source_created_at TEXT,
  source_updated_at TEXT,
  raw_response TEXT,
  synced_at TEXT,
  created_at TEXT
);
CREATE TABLE compliance__claude_roles (
  id INTEGER NOT NULL,
  organization_id INTEGER,
  role_data TEXT,
  synced_at TEXT,
  created_at TEXT
);
CREATE TABLE compliance__claude_sync_state (
  id INTEGER NOT NULL,
  job_name TEXT NOT NULL,
  last_cursor TEXT,
  last_run_at TEXT,
  records_synced INTEGER,
  last_error TEXT,
  created_at TEXT
);
CREATE TABLE compliance__claude_users (
  id INTEGER NOT NULL,
  claude_user_id TEXT NOT NULL,
  organization_id INTEGER,
  full_name TEXT,
  email TEXT,
  source_created_at TEXT,
  raw_response TEXT,
  synced_at TEXT,
  created_at TEXT
);
CREATE TABLE agent__facet_cache (
  session_id TEXT NOT NULL,
  account_uuid TEXT,
  facets TEXT NOT NULL,
  model_used TEXT,
  extracted_at TEXT NOT NULL
);
CREATE TABLE agent__outputs (
  id INTEGER NOT NULL,
  filename TEXT NOT NULL,
  account_uuid TEXT,
  agent_type TEXT NOT NULL,
  output_type TEXT NOT NULL,
  run_id INTEGER,
  content TEXT NOT NULL,
  size_bytes INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE agent__runs (
  id INTEGER NOT NULL,
  run_uuid TEXT NOT NULL,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  agent_type TEXT NOT NULL,
  agent_version TEXT,
  invocation_method TEXT NOT NULL,
  triggered_by TEXT,
  account_uuid TEXT,
  target_email TEXT,
  target_month TEXT,
  prompt TEXT,
  requested_schema TEXT,
  status TEXT NOT NULL,
  error TEXT,
  total_cost_usd REAL,
  total_tokens_in INTEGER,
  total_tokens_out INTEGER,
  total_duration_ms INTEGER,
  total_turns INTEGER,
  total_api_calls INTEGER,
  case_count INTEGER,
  session_count INTEGER,
  persona_version INTEGER,
  generated_sql TEXT,
  result_row_count INTEGER,
  result_truncated INTEGER,
  primary_model TEXT,
  model_usage TEXT
);
CREATE TABLE agent__stages (
  id INTEGER NOT NULL,
  run_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  stage_number INTEGER NOT NULL,
  stage_name TEXT NOT NULL,
  model TEXT,
  budget_usd REAL,
  status TEXT NOT NULL,
  error TEXT,
  cost_usd REAL,
  tokens_in INTEGER,
  tokens_out INTEGER,
  duration_ms INTEGER,
  api_calls INTEGER,
  turns INTEGER,
  sessions_processed INTEGER,
  facets_extracted INTEGER,
  facets_cached INTEGER,
  cases_grouped INTEGER,
  sections_generated INTEGER,
  persona_version_out INTEGER,
  output_filename TEXT,
  model_usage TEXT,
  section_costs TEXT
);
CREATE INDEX idx_cowork__sessions_account_uuid ON cowork__sessions(account_uuid);
CREATE INDEX idx_compliance__claude_chats_organization_id ON compliance__claude_chats(organization_id);
CREATE INDEX idx_compliance__claude_activities_organization_id ON compliance__claude_activities(organization_id);
CREATE INDEX idx_agent__runs_agent_type ON agent__runs(agent_type);
CREATE INDEX idx_agent__runs_status ON agent__runs(status);
CREATE INDEX idx_agent__outputs_run_id ON agent__outputs(run_id);
