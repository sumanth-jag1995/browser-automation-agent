export interface Settings {
  openrouterApiKey: string;
  openrouterModel: string;
  useMockLlm: boolean;
  maxRetries: number;
  maxRepairBeforeRegenerate: number;
}

export const DEFAULT_SETTINGS: Settings = {
  openrouterApiKey: '',
  openrouterModel: 'anthropic/claude-haiku-4-5',
  useMockLlm: false,
  maxRetries: 3,
  maxRepairBeforeRegenerate: 2,
};

export interface RunRequest {
  url: string;
  intent: string;
  openrouter_api_key?: string;
  openrouter_model?: string;
  use_mock_llm?: boolean;
  max_retries?: number;
  max_repair_before_regenerate?: number;
}

export interface RunResponse {
  run_id: string;
  status: string;
  dashboard_url: string;
}

export interface StatusResponse {
  status: string;
  progress: number;
}

export interface ExecutionResult {
  flow: string;
  status: string;
  home_page_verified?: boolean;
  error?: string;
}

export interface Report {
  run_id: string;
  url: string;
  intent: string;
  status: string;
  flows_total?: number;
  flows_passed?: number;
  auto_repairs?: number;
  retries_used?: number;
  regressions?: number;
  execution_results?: ExecutionResult[];
  screenshots?: string[];
  generated_at?: string;
  dashboard_url?: string;
  human_escalation?: boolean;
}

export interface RunSummary {
  run_id: string;
  intent: string;
  status: string;
  flows_total: number;
  flows_passed: number;
  generated_at: string;
}

export interface LogEntry {
  timestamp: string;
  message: string;
}
