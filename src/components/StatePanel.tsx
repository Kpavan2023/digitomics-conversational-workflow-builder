import type {
  Requirement,
  WorkflowState,
} from '@/lib/types';

import {
  Check,
  HelpCircle,
  AlertTriangle,
  CircleDot,
} from 'lucide-react';

interface StatePanelProps {
  state: WorkflowState;
  requirements: Requirement[];
}

export function StatePanel({
  state,
  requirements,
}: StatePanelProps) {
  const totalRequired = requirements.filter(
    (requirement) => requirement.required
  ).length;

  const satisfiedRequired = requirements.filter(
    (requirement) =>
      requirement.required &&
      requirement.status === 'satisfied'
  ).length;

  const progress =
    totalRequired > 0
      ? Math.round(
          (satisfiedRequired / totalRequired) * 100
        )
      : 0;

  const isReady =
    state.status === 'ready' ||
    state.status === 'generated';

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-4 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
          Collected Information
        </h2>

        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-sky-500 rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
              }}
            />
          </div>

          <span className="text-xs font-medium text-slate-500">
            {progress}%
          </span>
        </div>

        <div className="mt-2 flex items-center gap-2">
          {isReady ? (
            <>
              <CircleDot className="w-4 h-4 text-emerald-500" />

              <span className="text-xs font-medium text-emerald-600">
                Workflow Ready
              </span>
            </>
          ) : (
            <>
              <CircleDot className="w-4 h-4 text-amber-500" />

              <span className="text-xs font-medium text-amber-600">
                Collecting requirements...
              </span>
            </>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        {requirements.map((requirement) => {
          const isSatisfied =
            requirement.status === 'satisfied';

          const isAmbiguous =
            requirement.status === 'ambiguous';

          const isConflicting =
            requirement.status === 'conflicting';

          return (
            <div
              key={requirement.id}
              className="flex items-start gap-3"
            >
              <div className="flex-shrink-0 mt-0.5">
                {isSatisfied ? (
                  <Check className="w-4 h-4 text-emerald-500" />
                ) : isAmbiguous ||
                  isConflicting ? (
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                ) : (
                  <HelpCircle className="w-4 h-4 text-slate-300" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-500">
                  {requirement.description}
                </p>

                {isSatisfied ? (
                  <p className="text-sm text-emerald-600">
                    Provided
                  </p>
                ) : isAmbiguous ? (
                  <p className="text-sm text-amber-600 italic">
                    Ambiguous — needs clarification
                  </p>
                ) : isConflicting ? (
                  <p className="text-sm text-rose-600 italic">
                    Conflicting — needs clarification
                  </p>
                ) : (
                  <p className="text-sm text-slate-300 italic">
                    Not yet provided
                  </p>
                )}
              </div>
            </div>
          );
        })}

        {requirements.length === 0 && (
          <div className="text-sm text-slate-400 text-center py-8">
            No requirements identified yet.
          </div>
        )}

        {state.ambiguities.length > 0 && (
          <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-amber-500" />

              <p className="text-xs font-semibold text-amber-700">
                Clarifications Needed
              </p>
            </div>

            <ul className="space-y-1">
              {state.ambiguities.map(
                (ambiguity, index) => (
                  <li
                    key={index}
                    className="text-xs text-amber-600"
                  >
                    {ambiguity}
                  </li>
                )
              )}
            </ul>
          </div>
        )}

        {state.conflicts.length > 0 && (
          <div className="mt-4 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-rose-500" />

              <p className="text-xs font-semibold text-rose-700">
                Conflicts
              </p>
            </div>

            <ul className="space-y-1">
              {state.conflicts.map(
                (conflict, index) => (
                  <li
                    key={index}
                    className="text-xs text-rose-600"
                  >
                    {conflict}
                  </li>
                )
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}