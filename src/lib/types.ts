// Canonical frontend types.
//
// The FastAPI backend owns workflow interpretation,
// requirement evaluation, completeness, and workflow generation.
// The frontend only represents and displays the backend state.

export type WorkflowStatus =
  | 'collecting'
  | 'ready'
  | 'generated';

export type MessageRole =
  | 'user'
  | 'assistant'
  | 'system';

export interface Intent {
  goal: string | null;
  confidence: number | null;
}

export interface Trigger {
  type: string | null;
  provider: string | null;
  configuration: Record<string, unknown>;
}

export interface Condition {
  field: string;
  operator: string;
  value: unknown;
  currency: string | null;
}

export interface Action {
  type: string;
  provider: string | null;
  configuration: Record<string, unknown>;
}

export interface WorkflowState {
  intent: Intent;
  trigger: Trigger;
  conditions: Condition[];
  actions: Action[];
  missing_requirements: string[];
  ambiguities: string[];
  conflicts: string[];
  status: WorkflowStatus;
  version: number;
}

export interface Requirement {
  id: string;
  description: string;
  status:
    | 'missing'
    | 'satisfied'
    | 'ambiguous'
    | 'conflicting';
  required: boolean;
  depends_on: string[];
  question: string | null;
  priority: number;
}

export interface ChatMessage {
  id?: string | null;
  role: MessageRole;
  content: string;
  created_at?: string | null;
  metadata?: Record<string, unknown>;
}

export interface WorkflowNode {
  id: string;
  type: string;
  label: string;
  configuration: Record<string, unknown>;
}

export interface WorkflowEdge {
  from_node: string;
  to_node: string;
}

export interface WorkflowMetadata {
  name: string | null;
  description: string | null;
}

export interface GeneratedWorkflow {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  metadata: WorkflowMetadata;
}

export interface Conversation {
  id: string;
  title: string | null;
  messages: ChatMessage[];
  state: WorkflowState;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ChatResponse {
  message: string;
  workflow_ready: boolean;
  state: WorkflowState;
  requirements: Requirement[];
  ambiguities: string[];
  conflicts: string[];
}

export interface WorkflowResponse {
  workflow: GeneratedWorkflow | null;
  valid: boolean;
  errors: string[];
}

export function emptyState(): WorkflowState {
  return {
    intent: {
      goal: null,
      confidence: null,
    },

    trigger: {
      type: null,
      provider: null,
      configuration: {},
    },

    conditions: [],

    actions: [],

    missing_requirements: [],

    ambiguities: [],

    conflicts: [],

    status: 'collecting',

    version: 1,
  };
}