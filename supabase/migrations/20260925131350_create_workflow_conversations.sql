/*
# Create workflow conversations storage

1. New Tables
- `workflow_conversations` stores the single-tenant MVP's conversation transcript, canonical workflow state, and last generated workflow as JSON.
- `id` is the durable conversation identifier.
- `title` is the user-facing conversation label.
- `messages` stores role/content/timestamp entries for resume support.
- `state` stores the deterministic workflow state owned by the application.
- `workflow` stores the validated graph once requirements are complete.
- `status` stores collecting or ready state.
- `created_at` and `updated_at` track lifecycle timestamps.
2. Security
- Row level security is enabled.
- This MVP has no sign-in screen and intentionally uses anon + authenticated policies so the shared demo can create, read, update, and delete its conversations.
3. Important notes
- Workflow JSON is stored as data only; nothing in this table is executed.
- The table is intentionally small and can be split into normalized message/state tables when multi-user accounts are introduced.
*/

CREATE TABLE IF NOT EXISTS workflow_conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL DEFAULT 'Untitled workflow',
  messages jsonb NOT NULL DEFAULT '[]'::jsonb,
  state jsonb NOT NULL DEFAULT '{}'::jsonb,
  workflow jsonb,
  status text NOT NULL DEFAULT 'collecting' CHECK (status IN ('collecting', 'ready')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE workflow_conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_workflow_conversations" ON workflow_conversations;
CREATE POLICY "anon_select_workflow_conversations" ON workflow_conversations FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_workflow_conversations" ON workflow_conversations;
CREATE POLICY "anon_insert_workflow_conversations" ON workflow_conversations FOR INSERT TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_workflow_conversations" ON workflow_conversations;
CREATE POLICY "anon_update_workflow_conversations" ON workflow_conversations FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_workflow_conversations" ON workflow_conversations;
CREATE POLICY "anon_delete_workflow_conversations" ON workflow_conversations FOR DELETE TO anon, authenticated USING (true);

CREATE INDEX IF NOT EXISTS workflow_conversations_updated_at_idx ON workflow_conversations (updated_at DESC);
