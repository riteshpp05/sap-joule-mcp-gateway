export interface HealthStatus {
  status: string;
  modes: string[];
  metrics: string;
  liveness: string;
  readiness: string;
}

export interface ReadinessStatus {
  status: string;
  mock_mode: boolean;
  sap_base_url: string;
  gateway_api_key_enabled: boolean;
  cors_origins: string[];
}

export interface DumpItem {
  dump_id: string;
  title: string;
  user: string;
  timestamp: string;
  program: string;
  runtime_error?: string;
}

export interface AutoFixProposal {
  dump_id: string;
  status: string;
  target_program: string;
  exception_type: string;
  original_code: string;
  proposed_code: string;
  ai_analysis: string;
  requires_user_approval: boolean;
  push_ready: boolean;
  user_controller_message: string;
}

export interface PushFixResult {
  program_name: string;
  pushed: boolean;
  status: string;
  rollback_performed?: boolean;
  lock_conflict?: boolean;
  locked_by?: string;
  message: string;
}

export interface CdsCreateResponse {
  view_name: string;
  view_type: 'entity' | 'classic';
  sql_view_name?: string | null;
  ddl: string;
  pushed: boolean;
  note?: string;
}

export interface AbapUnitTestResult {
  program_name: string;
  mock_mode: boolean;
  status: 'SUCCESS' | 'FAILED' | 'ERROR';
  tests_run: number;
  passed: number;
  failed: number;
  errors: number;
  details: Array<{
    test_class: string;
    method: string;
    status: 'PASSED' | 'FAILED' | 'ERROR';
    failure_detail?: string | null;
  }>;
  message: string;
}

export interface TransportValidationResult {
  valid: boolean;
  package: string;
  transport_request?: string | null;
  is_local: boolean;
  message: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
