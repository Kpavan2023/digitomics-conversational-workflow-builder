```text
project/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── api/
│       │   ├── routes_chat.py
│       │   ├── routes_conversations.py
│       │   └── routes_workflow.py
│       ├── core/
│       │   ├── config.py
│       │   ├── exceptions.py
│       │   └── logging.py
│       ├── db/
│       │   └── session.py
│       ├── llm/
│       │   ├── base.py
│       │   ├── provider.py
│       │   └── rule_based.py
│       ├── models/
│       │   └── conversation.py
│       ├── orchestrator/
│       │   └── conversation_orchestrator.py
│       ├── schemas/
│       │   ├── conversation.py
│       │   ├── extraction.py
│       │   ├── message.py
│       │   ├── requirement.py
│       │   └── workflow.py
│       └── services/
│           ├── ambiguity_service.py
│           ├── extraction_service.py
│           ├── intent_service.py
│           ├── normalization_service.py
│           ├── question_service.py
│           ├── requirement_service.py
│           ├── validation_service.py
│           └── workflow_service.py
│
├── src/
│   ├── App.tsx
│   ├── index.css
│   ├── main.tsx
│   ├── components/
│   │   ├── ChatPanel.tsx
│   │   ├── StatePanel.tsx
│   │   └── WorkflowPanel.tsx
│   └── lib/
│       ├── api.ts
│       └── types.ts
│
├── supabase/
│   └── migrations/
│       └── 20260925131350_create_workflow_conversations.sql
│
└── tests/
    ├── integration/
    │   └── test_conversation.py
    └── unit/
        ├── test_ambiguity.py
        ├── test_conversation_schema.py
        ├── test_extraction.py
        ├── test_normalization.py
        ├── test_question_service.py
        ├── test_requirements.py
        └── test_workflow_service.py
```
