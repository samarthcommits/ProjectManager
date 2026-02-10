import { useState } from 'react';
import { useProjectStore } from '@/stores/useProjectStore';
import { KanbanSwimlane } from './KanbanSwimlane';
import { cn } from '@/lib/utils';
import type { TicketStatus } from '@/types/project';

const statusColumns: { key: TicketStatus; label: string }[] = [
  { key: 'todo', label: 'To Do' },
  { key: 'in-progress', label: 'In Progress' },
  { key: 'in-review', label: 'In Review' },
  { key: 'done', label: 'Done' },
];

export function KanbanBoard() {
  const { tickets, teamMembers } = useProjectStore();
  const [selectedAssignee, setSelectedAssignee] = useState<string | null>(null);

  const assignees = teamMembers.map((m) => m.name);
  const filteredAssignees = selectedAssignee ? [selectedAssignee] : assignees;

  return (
    <div className="space-y-4">
      {/* Filter pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedAssignee(null)}
          className={cn(
            'rounded-full px-3 py-1.5 text-sm font-medium transition-colors whitespace-nowrap',
            !selectedAssignee
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:text-foreground'
          )}
        >
          All
        </button>
        {assignees.map((name) => (
          <button
            key={name}
            onClick={() => setSelectedAssignee(name === selectedAssignee ? null : name)}
            className={cn(
              'rounded-full px-3 py-1.5 text-sm font-medium transition-colors whitespace-nowrap',
              name === selectedAssignee
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            )}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Board grid */}
      <div className="overflow-x-auto">
        {/* Column headers */}
        <div className="grid grid-cols-[140px_repeat(4,minmax(180px,1fr))] gap-3 mb-3">
          <div />
          {statusColumns.map((col) => (
            <div key={col.key} className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2">
              {col.label}
              <span className="ml-1.5 text-muted-foreground/60">
                {
                  tickets.filter(
                    (t) => t.status === col.key && (selectedAssignee ? t.assignee === selectedAssignee : true)
                  ).length
                }
              </span>
            </div>
          ))}
        </div>

        {/* Swimlanes */}
        <div className="space-y-3">
          {filteredAssignees.map((assignee) => (
            <KanbanSwimlane
              key={assignee}
              assignee={assignee}
              tickets={tickets.filter((t) => t.assignee === assignee)}
              statusColumns={statusColumns}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
