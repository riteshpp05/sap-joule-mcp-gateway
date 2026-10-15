import {
  HealthStatus,
  ReadinessStatus,
  DumpItem,
  AutoFixProposal,
  PushFixResult,
  CdsCreateResponse,
  AbapUnitTestResult,
  TransportValidationResult,
  ChatMessage,
} from '../types/api';

const BASE_URL = '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    let errMsg = `Request failed: ${res.status} ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData.detail) errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      else if (errData.message) errMsg = errData.message;
    } catch {
      // ignore json parse error
    }
    throw new Error(errMsg);
  }
  return res.json();
}

export const api = {
  getHealth: () => fetchJson<HealthStatus>('/health'),
  getReadiness: () => fetchJson<ReadinessStatus>('/health/ready'),
  getMetrics: async () => {
    const res = await fetch('/metrics');
    return res.text();
  },

  listRecentDumps: async (maxResults = 20): Promise<DumpItem[]> => {
    try {
      const data = await fetchJson<any>(`/api/abap/dumps?max_results=${maxResults}`);
      const rawList = Array.isArray(data) ? data : (data?.dumps || []);
      return rawList.map((item: any) => ({
        dump_id: item.dump_id || item.id || 'DUMP_UNKNOWN',
        title: item.title || item.runtime_error || 'ST22 Short Dump',
        user: item.user || 'DEVELOPER',
        timestamp: item.timestamp || (item.date && item.time ? `${item.date} ${item.time}` : item.time || item.date || 'Recent'),
        program: item.program || 'UNKNOWN_PROG',
        runtime_error: item.runtime_error || item.title || '',
      }));
    } catch (err) {
      console.error('Failed to list ST22 dumps:', err);
      return [];
    }
  },

  getDumpDetail: (dumpId: string) =>
    fetchJson<Record<string, any>>('/api/abap/st22', {
      method: 'POST',
      body: JSON.stringify({ dump_id: dumpId }),
    }),

  proposeAutoFix: async (dumpId: string): Promise<AutoFixProposal> => {
    const res = await fetchJson<any>('/api/abap/auto_fix', {
      method: 'POST',
      body: JSON.stringify({ dump_id: dumpId }),
    });

    const targetProgram = res.target_program || 'ZTEST_PROGRAM';
    const suggestedFix = res.suggested_fix || res.proposed_code || '';
    const originalCode =
      res.original_code ||
      `* Original Faulty ABAP Source (${targetProgram})\nREPORT ${targetProgram}.\n\n* Runtime Error: ${res.exception_type || 'ST22 Exception'}\n* Terminated during execution.`;

    return {
      dump_id: res.dump_id || dumpId,
      status: res.status || 'PROPOSED',
      target_program: targetProgram,
      exception_type: res.exception_type || 'CX_ROOT',
      original_code: originalCode,
      proposed_code: suggestedFix,
      ai_analysis: res.ai_analysis || res.fix_explanation || res.user_controller_message || 'Rule-based remediation synthesized.',
      requires_user_approval: res.requires_user_approval ?? true,
      push_ready: res.push_ready ?? true,
      user_controller_message: res.user_controller_message || 'Please review the proposed fix before pushing to SAP.',
    };
  },

  pushAbapFix: (payload: {
    program_name: string;
    fixed_code: string;
    dump_id?: string;
    confirm_push: boolean;
    package?: string;
    transport_request?: string;
    run_unit_tests?: boolean;
    auto_rollback_on_test_failure?: boolean;
  }) =>
    fetchJson<PushFixResult>('/api/abap/push_fix', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  runAbapUnitTests: (programName: string) =>
    fetchJson<AbapUnitTestResult>('/api/abap/unit_tests', {
      method: 'POST',
      body: JSON.stringify({ program_name: programName }),
    }),

  validateTransportRequest: (payload: {
    package: string;
    transport_request?: string;
  }) =>
    fetchJson<TransportValidationResult>('/api/cts/validate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  createPackage: (payload: {
    package_name: string;
    description?: string;
    super_package?: string;
    push_to_sap?: boolean;
    transport_request?: string;
  }) =>
    fetchJson<any>('/api/package/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  createCdsView: (payload: {
    view_name: string;
    table_name: string;
    fields: string[];
    joins?: Array<{ table: string; alias?: string; join_type?: string; on: string }>;
    associations?: Array<{ target: string; alias?: string; cardinality?: string; on: string }>;
    view_type?: 'entity' | 'classic';
    sql_view_name?: string;
    expose_to_fiori?: boolean;
    push_to_sap?: boolean;
    package?: string;
    transport_request?: string;
  }) =>
    fetchJson<CdsCreateResponse>('/api/cds/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  generateCdsFromEnglish: (promptText: string) =>
    fetchJson<Record<string, any>>('/api/ai/cds_from_english', {
      method: 'POST',
      body: JSON.stringify({ prompt: promptText }),
    }),

  summarizeAbapLogic: (code: string) =>
    fetchJson<{ summary: string }>('/api/ai/summarize_abap', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),

  explainCdsDiagnosis: (errorText: string) =>
    fetchJson<{ diagnosis: string }>('/api/ai/explain_cds_diagnosis', {
      method: 'POST',
      body: JSON.stringify({ error: errorText }),
    }),

  sendChat: (messages: ChatMessage[]) =>
    fetchJson<{ reply: string }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ messages }),
    }),
};
