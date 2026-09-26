/**
 * API service layer — talks to the Python FastAPI backend.
 *
 * The FastAPI backend is the single source of truth for:
 * - conversation processing
 * - information extraction
 * - requirement analysis
 * - clarification questions
 * - workflow generation
 * - workflow validation
 */

import type {
  ChatMessage,
  WorkflowState,
  GeneratedWorkflow,
} from './types';

const API_BASE =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

interface BackendConversationResponse {
  id: string;
  title: string;
  messages: ChatMessage[];
  state: WorkflowState;
  created_at?: string | null;
  updated_at?: string | null;
}

interface BackendChatResponse {
  message: string;
  workflow_ready: boolean;
  state: WorkflowState;
  workflow: GeneratedWorkflow | null;
  requirements: unknown[];
  ambiguities: string[];
  conflicts: string[];
}

export const api = {
  /**
   * Create a new workflow-building conversation.
   */
  async createConversation(): Promise<{
    id: string;
    messages: ChatMessage[];
    state: WorkflowState;
  }> {
    const res = await apiFetch('/conversations', {
      method: 'POST',
      body: JSON.stringify({}),
    });

    const data: BackendConversationResponse =
      await res.json();

    return {
      id: data.id,
      messages: data.messages,
      state: data.state,
    };
  },

  /**
   * Send a user message to the FastAPI conversation orchestrator.
   *
   * The backend returns the generated workflow directly
   * when all required information has been collected.
   */
  async sendMessage(
    conversationId: string,
    content: string
  ): Promise<{
    assistantMessage: string;
    workflowReady: boolean;
    state: WorkflowState;
    workflow: GeneratedWorkflow | null;
    requirements: unknown[];
    ambiguities: string[];
    conflicts: string[];
  }> {
    const res = await apiFetch(
      `/chat/${conversationId}/messages`,
      {
        method: 'POST',
        body: JSON.stringify({
          message: content,
        }),
      }
    );

    const data: BackendChatResponse =
      await res.json();

    return {
      assistantMessage: data.message,
      workflowReady: data.workflow_ready,
      state: data.state,
      workflow: data.workflow,
      requirements: data.requirements,
      ambiguities: data.ambiguities,
      conflicts: data.conflicts,
    };
  },

  /**
   * Retrieve the current workflow state and requirements.
   */
  async getWorkflowState(
    conversationId: string
  ): Promise<{
    state: WorkflowState;
    requirements: unknown[];
  }> {
    const res = await apiFetch(
      `/workflows/${conversationId}/state`
    );

    return res.json();
  },
};

async function apiFetch(
  path: string,
  options?: RequestInit
): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!res.ok) {
    let detail = `API error: ${res.status}`;

    try {
      const body = await res.json();

      if (typeof body?.detail === 'string') {
        detail = body.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(detail);
  }

  return res;
}