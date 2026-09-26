import {
  useEffect,
  useRef,
  useState,
} from 'react';

import type { ChatMessage } from '@/lib/types';

import {
  Bot,
  User,
} from 'lucide-react';

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
  onReset: () => void;
}

export function ChatPanel({
  messages,
  loading,
  onSend,
  onReset,
}: ChatPanelProps) {
  const inputRef =
    useRef<HTMLTextAreaElement>(null);

  const scrollRef =
    useRef<HTMLDivElement>(null);

  /*
   * Controlled input state.
   *
   * This is important because React needs to
   * re-render when the user types so that the
   * Send button can correctly become enabled.
   */
  const [input, setInput] =
    useState('');

  /*
   * Automatically scroll to the newest message
   * whenever messages or loading state changes.
   */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop =
        scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  /*
   * Send the current message.
   */
  const handleSend = () => {
    const text = input.trim();

    if (!text || loading) {
      return;
    }

    onSend(text);

    /*
     * Clear the controlled input after sending.
     */
    setInput('');

    /*
     * Return focus to the textarea.
     */
    requestAnimationFrame(() => {
      inputRef.current?.focus();
    });
  };

  /*
   * Enter = send
   *
   * Shift + Enter = new line
   */
  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      e.key === 'Enter' &&
      !e.shiftKey
    ) {
      e.preventDefault();

      handleSend();
    }
  };

  /*
   * Send button is disabled only when:
   * - backend is processing a message, or
   * - there is no actual text to send.
   */
  const sendDisabled =
    loading || !input.trim();

  return (
    <div className="flex h-full flex-col">

      {/* =====================================================
          MESSAGE AREA
          ===================================================== */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6 space-y-4"
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-slate-400">

            <Bot className="w-12 h-12 mb-3 text-slate-300" />

            <p className="text-sm max-w-xs">
              Describe the automation you want
              to build. I'll ask clarifying
              questions until I have everything
              needed to generate a workflow.
            </p>

          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${
              msg.role === 'user'
                ? 'flex-row-reverse'
                : ''
            }`}
          >
            {/* Avatar */}
            <div
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                msg.role === 'user'
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-200 text-slate-700'
              }`}
            >
              {msg.role === 'user' ? (
                <User className="w-4 h-4" />
              ) : (
                <Bot className="w-4 h-4" />
              )}
            </div>

            {/* Message */}
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-sky-600 text-white rounded-tr-sm'
                  : 'bg-white text-slate-700 rounded-tl-sm shadow-sm border border-slate-200'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* =================================================
            LOADING INDICATOR
            ================================================= */}
        {loading && (
          <div className="flex gap-3">

            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>

            <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-slate-200 px-4 py-3">

              <div className="flex gap-1">

                <span
                  className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"
                  style={{
                    animationDelay: '0ms',
                  }}
                />

                <span
                  className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"
                  style={{
                    animationDelay: '150ms',
                  }}
                />

                <span
                  className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"
                  style={{
                    animationDelay: '300ms',
                  }}
                />

              </div>

            </div>

          </div>
        )}
      </div>

      {/* =====================================================
          INPUT AREA
          ===================================================== */}
      <div className="border-t border-slate-200 px-4 py-3 bg-white">

        <div className="flex gap-2 items-end">

          {/* Message input */}
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            placeholder="Type your message..."
            className="flex-1 resize-none rounded-xl border border-slate-300 px-4 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent max-h-32"
            onChange={(e) =>
              setInput(e.target.value)
            }
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          {/* Send */}
          <button
            type="button"
            onClick={handleSend}
            disabled={sendDisabled}
            className="rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>

          {/* New conversation */}
          <button
            type="button"
            onClick={onReset}
            disabled={loading}
            className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40 transition-colors"
          >
            New
          </button>

        </div>

      </div>

    </div>
  );
}