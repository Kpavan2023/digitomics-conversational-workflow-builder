import { useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  type Node,
  type Edge,
  Position,
} from 'reactflow';

import 'reactflow/dist/style.css';

import type { GeneratedWorkflow } from '@/lib/types';

import {
  Workflow,
  Code2,
  Download,
} from 'lucide-react';

interface WorkflowPanelProps {
  workflow: GeneratedWorkflow | null;
  onRefine: () => void;
  onReset: () => void;
}

const NODE_COLORS: Record<string, string> = {
  trigger: '#0ea5e9',
  condition: '#f59e0b',
  action: '#10b981',
  end: '#94a3b8',
};

const NODE_TYPE_LABELS: Record<string, string> = {
  trigger: 'TRIGGER',
  condition: 'CONDITION',
  action: 'ACTION',
  end: 'END',
};

function toReactFlowNodes(
  workflow: GeneratedWorkflow
): {
  nodes: Node[];
  edges: Edge[];
} {
  const verticalSpacing = 120;
  const startY = 20;

  const nodes: Node[] = workflow.nodes.map(
    (node, index) => ({
      id: node.id,
      type: 'default',

      position: {
        x: 200,
        y: startY + index * verticalSpacing,
      },

      data: {
        label: (
          <div className="text-center px-2 py-1">
            <div
              className="text-[10px] font-mono uppercase opacity-60"
              style={{
                color:
                  NODE_COLORS[node.type] ??
                  '#94a3b8',
              }}
            >
              {NODE_TYPE_LABELS[node.type] ??
                node.type}
            </div>

            <div className="text-sm font-medium text-slate-700">
              {node.label}
            </div>
          </div>
        ),
      },

      style: {
        border: `2px solid ${
          NODE_COLORS[node.type] ??
          '#94a3b8'
        }`,
        borderRadius: '12px',
        background: '#fff',
        padding: '4px',
        width: 220,
      },

      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    })
  );

  const edges: Edge[] = workflow.edges.map(
    (edge, index) => ({
      id: `edge-${index}`,

      source: edge.from_node,
      target: edge.to_node,

      type: 'smoothstep',

      style: {
        stroke: '#cbd5e1',
        strokeWidth: 2,
      },
    })
  );

  return {
    nodes,
    edges,
  };
}

export function WorkflowPanel({
  workflow,
  onRefine,
  onReset,
}: WorkflowPanelProps) {
  const [view, setView] =
    useState<'graph' | 'json'>('graph');

  if (!workflow) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6">
        <Workflow className="w-12 h-12 text-slate-200 mb-3" />

        <p className="text-sm text-slate-400 max-w-xs">
          Once all requirements are collected,
          the generated workflow will appear here.
        </p>
      </div>
    );
  }

  const downloadJson = () => {
    const blob = new Blob(
      [JSON.stringify(workflow, null, 2)],
      {
        type: 'application/json',
      }
    );

    const url =
      URL.createObjectURL(blob);

    const anchor =
      document.createElement('a');

    anchor.href = url;
    anchor.download = 'workflow.json';

    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    URL.revokeObjectURL(url);
  };

  const {
    nodes,
    edges,
  } = toReactFlowNodes(workflow);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Generated Workflow
          </h2>

          <div className="flex gap-1 rounded-lg bg-slate-100 p-0.5">
            <button
              onClick={() =>
                setView('graph')
              }
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                view === 'graph'
                  ? 'bg-white text-slate-700 shadow-sm'
                  : 'text-slate-500'
              }`}
            >
              <Workflow className="w-3.5 h-3.5 inline mr-1" />

              Graph
            </button>

            <button
              onClick={() =>
                setView('json')
              }
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                view === 'json'
                  ? 'bg-white text-slate-700 shadow-sm'
                  : 'text-slate-500'
              }`}
            >
              <Code2 className="w-3.5 h-3.5 inline mr-1" />

              JSON
            </button>
          </div>
        </div>

        <p className="mt-2 text-sm text-slate-600 font-medium">
          {workflow.metadata.name ??
            'Generated Workflow'}
        </p>

        {workflow.metadata.description && (
          <p className="mt-1 text-xs text-slate-400">
            {workflow.metadata.description}
          </p>
        )}
      </div>

      {/* Workflow visualization */}
      <div className="flex-1 overflow-hidden">
        {view === 'graph' ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            fitViewOptions={{
              padding: 0.2,
            }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            panOnScroll
            zoomOnScroll={false}
          >
            <Background
              color="#e2e8f0"
              gap={16}
            />

            <Controls
              showInteractive={false}
            />
          </ReactFlow>
        ) : (
          <pre className="text-xs text-slate-700 bg-slate-50 p-4 overflow-auto font-mono leading-relaxed h-full">
            {JSON.stringify(
              workflow,
              null,
              2
            )}
          </pre>
        )}
      </div>

      {/* Actions */}
      <div className="border-t border-slate-200 px-5 py-3 flex gap-2">
        <button
          onClick={downloadJson}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors flex items-center justify-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5" />

          Export JSON
        </button>

        <button
          onClick={onRefine}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
        >
          Edit / Refine
        </button>

        <button
          onClick={onReset}
          className="flex-1 rounded-lg bg-sky-600 px-3 py-2 text-xs font-medium text-white hover:bg-sky-700 transition-colors"
        >
          Start New
        </button>
      </div>
    </div>
  );
}