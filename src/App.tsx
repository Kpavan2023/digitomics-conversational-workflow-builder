import { useState, useCallback } from 'react';
import {
  Bot,
  MessageSquare,
  ChevronRight,
} from 'lucide-react';

import type {
  ChatMessage,
  WorkflowState,
  GeneratedWorkflow,
  Requirement,
} from '@/lib/types';

import { emptyState } from '@/lib/types';
import { api } from '@/lib/api';

import { ChatPanel } from '@/components/ChatPanel';
import { StatePanel } from '@/components/StatePanel';
import { WorkflowPanel } from '@/components/WorkflowPanel';

function makeMessage(
  role: 'user' | 'assistant',
  content: string
): ChatMessage {
  return {
    id: `${Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 8)}`,
    role,
    content,
    created_at: new Date().toISOString(),
  };
}

const WELCOME =
  "I can help you build an automation workflow. Describe what you'd like to automate — for example, 'When I receive an invoice above ₹10,000, notify finance on Slack.' I'll ask clarifying questions until I have everything needed.";

function App() {
  const [conversationId, setConversationId] =
    useState<string | null>(null);

  const [messages, setMessages] = useState<
    ChatMessage[]
  >([
    makeMessage('assistant', WELCOME),
  ]);

  const [state, setState] =
    useState<WorkflowState>(emptyState());

  const [requirements, setRequirements] =
    useState<Requirement[]>([]);

  const [workflow, setWorkflow] =
    useState<GeneratedWorkflow | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [showMobilePanel, setShowMobilePanel] =
    useState<'state' | 'workflow' | null>(null);

  /*
   * Create the conversation lazily.
   *
   * We only create a backend conversation when
   * the user actually sends their first message.
   */
  const ensureConversation = useCallback(
    async (): Promise<string> => {
      if (conversationId) {
        return conversationId;
      }

      const conversation =
        await api.createConversation();

      setConversationId(conversation.id);

      return conversation.id;
    },
    [conversationId]
  );

  /*
   * Send a user message to the backend.
   *
   * The FastAPI backend is the single source of truth
   * for:
   * - extraction
   * - requirement evaluation
   * - clarification questions
   * - workflow completeness
   * - workflow generation
   */
  const handleSend = useCallback(
    async (text: string) => {
      const userMessage = makeMessage(
        'user',
        text
      );

      /*
       * Immediately show the user's message
       * in the chat UI.
       */
      setMessages((current) => [
        ...current,
        userMessage,
      ]);

      setLoading(true);

      try {
        const id =
          await ensureConversation();

        /*
         * Send the message to FastAPI.
         */
        const result =
          await api.sendMessage(id, text);

        /*
         * Update canonical workflow state
         * returned by the backend.
         */
        setState(result.state);

        /*
         * Update requirement statuses/questions
         * returned by the backend.
         */
        setRequirements(
          result.requirements as Requirement[]
        );

        /*
         * Add the backend's assistant response
         * to the conversation.
         */
        const assistantMessage =
          makeMessage(
            'assistant',
            result.assistantMessage
          );

        setMessages((current) => [
          ...current,
          assistantMessage,
        ]);

        /*
         * The backend generates a workflow only
         * after all required information has been
         * collected.
         *
         * The generated workflow is already included
         * in this response, so there is NO second
         * GET /workflows request.
         */
        if (result.workflowReady) {
          setWorkflow(result.workflow);
        } else {
          /*
           * While collecting information, there is
           * no generated workflow to display.
           */
          setWorkflow(null);
        }
      } catch (error) {
        console.error(
          'Failed to process message:',
          error
        );

        const errorMessage =
          makeMessage(
            'assistant',
            'I could not connect to the workflow backend. Please check that the FastAPI server is running and try again.'
          );

        setMessages((current) => [
          ...current,
          errorMessage,
        ]);
      } finally {
        setLoading(false);
      }
    },
    [ensureConversation]
  );

  /*
   * Completely reset the current workflow-building
   * session.
   */
  const handleReset = useCallback(() => {
    setConversationId(null);

    setMessages([
      makeMessage(
        'assistant',
        WELCOME
      ),
    ]);

    setState(emptyState());

    setRequirements([]);

    setWorkflow(null);

    setShowMobilePanel(null);
  }, []);

  /*
   * Refine means:
   * - keep the existing conversation
   * - remove the displayed generated workflow
   * - let the next user message go back through
   *   the backend orchestrator.
   *
   * The frontend does NOT modify workflow state.
   */
  const handleRefine = useCallback(() => {
    setWorkflow(null);
    setShowMobilePanel(null);
  }, []);

  /*
   * Workflow is considered ready when the backend
   * state is ready or generated.
   */
  const isReady =
    state.status === 'ready' ||
    state.status === 'generated';

  return (
    <div className="h-screen flex flex-col bg-slate-100">

      {/* =====================================================
          HEADER
          ===================================================== */}
      <header className="flex-shrink-0 bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">

        <div className="flex items-center gap-2.5">

          {/* Application icon */}
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-cyan-500 flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>

          {/* Application title */}
          <div>
            <h1 className="text-base font-semibold text-slate-800">
              Workflow Builder
            </h1>

            <p className="text-xs text-slate-400">
              Intelligent conversational planning
            </p>
          </div>

        </div>

        {/* Workflow status */}
        <div className="flex items-center gap-2">

          <span
            className={`text-xs font-medium px-3 py-1.5 rounded-full ${
              isReady
                ? 'bg-emerald-50 text-emerald-600'
                : 'bg-amber-50 text-amber-600'
            }`}
          >
            {isReady
              ? 'Workflow Ready'
              : 'Collecting'}
          </span>

        </div>

      </header>

      {/* =====================================================
          MAIN CONTENT
          ===================================================== */}
      <div className="flex-1 flex overflow-hidden">

        {/* ===================================================
            CHAT PANEL
            =================================================== */}
        <main className="flex-1 flex flex-col bg-slate-50 min-w-0">

          <ChatPanel
            messages={messages}
            loading={loading}
            onSend={handleSend}
            onReset={handleReset}
          />

        </main>

        {/* ===================================================
            STATE PANEL — DESKTOP
            =================================================== */}
        <aside className="hidden lg:flex w-72 flex-shrink-0 bg-white border-l border-slate-200">

          <StatePanel
            state={state}
            requirements={requirements}
          />

        </aside>

        {/* ===================================================
            WORKFLOW PANEL — DESKTOP
            =================================================== */}
        <aside className="hidden lg:flex w-96 flex-shrink-0 bg-white border-l border-slate-200">

          <WorkflowPanel
            workflow={workflow}
            onRefine={handleRefine}
            onReset={handleReset}
          />

        </aside>

      </div>

      {/* =====================================================
          MOBILE PANEL NAVIGATION
          ===================================================== */}
      <div className="lg:hidden flex-shrink-0 bg-white border-t border-slate-200 px-4 py-2 flex gap-2">

        {/* Collected information */}
        <button
          onClick={() =>
            setShowMobilePanel(
              showMobilePanel === 'state'
                ? null
                : 'state'
            )
          }
          className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium ${
            showMobilePanel === 'state'
              ? 'bg-sky-600 text-white'
              : 'text-slate-600 bg-slate-100'
          }`}
        >

          <MessageSquare className="w-3.5 h-3.5" />

          Collected Info

          <ChevronRight className="w-3 h-3" />

        </button>

        {/* Workflow */}
        <button
          onClick={() =>
            setShowMobilePanel(
              showMobilePanel === 'workflow'
                ? null
                : 'workflow'
            )
          }
          className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-medium ${
            showMobilePanel === 'workflow'
              ? 'bg-sky-600 text-white'
              : 'text-slate-600 bg-slate-100'
          }`}
        >

          <Bot className="w-3.5 h-3.5" />

          Workflow

          <ChevronRight className="w-3 h-3" />

        </button>

      </div>

      {/* =====================================================
          MOBILE SIDE PANEL
          ===================================================== */}
      {showMobilePanel && (

        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/30"
          onClick={() =>
            setShowMobilePanel(null)
          }
        >

          <div
            className="absolute right-0 top-0 bottom-0 w-80 max-w-[85vw] bg-white shadow-xl"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            {/* Collected information */}
            {showMobilePanel === 'state' && (

              <StatePanel
                state={state}
                requirements={requirements}
              />

            )}

            {/* Generated workflow */}
            {showMobilePanel === 'workflow' && (

              <WorkflowPanel
                workflow={workflow}
                onRefine={handleRefine}
                onReset={handleReset}
              />

            )}

          </div>

        </div>

      )}

    </div>
  );
}

export default App;