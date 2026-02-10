import { useState } from 'react';
import { X, CheckSquare, Square, Code2, MessageSquare } from 'lucide-react';
import { useProjectStore } from '@/stores/useProjectStore';
import { CommentSection } from './CommentSection';
import { cn } from '@/lib/utils';
import type { Ticket, Priority, TicketStatus } from '@/types/project';

const priorityOptions: { value: Priority; label: string }[] = [
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const statusOptions: { value: TicketStatus; label: string }[] = [
  { value: 'todo', label: 'To Do' },
  { value: 'in-progress', label: 'In Progress' },
  { value: 'in-review', label: 'In Review' },
  { value: 'done', label: 'Done' },
];

interface TicketDetailModalProps {
  ticket: Ticket;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TicketDetailModal({ ticket, open, onOpenChange }: TicketDetailModalProps) {
  const { updateTicket, teamMembers } = useProjectStore();
  const [checkedCriteria, setCheckedCriteria] = useState<Set<number>>(new Set());

  if (!open) return null;

  const toggleCriteria = (index: number) => {
    setCheckedCriteria((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={(e) => e.stopPropagation()}>
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={() => onOpenChange(false)} />
      <div className="relative w-full max-w-2xl bg-card border-l border-border overflow-y-auto animate-slide-in-right">
        {/* Header */}
        <div className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur-sm px-6 py-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-mono text-muted-foreground mb-1">{ticket.ticketId}</p>
              <h2 className="text-lg font-semibold">{ticket.title}</h2>
            </div>
            <button
              onClick={() => onOpenChange(false)}
              className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex flex-wrap gap-3 mt-3">
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Status</label>
              <select
                value={ticket.status}
                onChange={(e) => updateTicket(ticket.id, { status: e.target.value as TicketStatus })}
                className="block w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {statusOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Assignee</label>
              <select
                value={ticket.assignee}
                onChange={(e) => updateTicket(ticket.id, { assignee: e.target.value })}
                className="block w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {teamMembers.map((m) => (
                  <option key={m.id} value={m.name}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Priority</label>
              <select
                value={ticket.priority}
                onChange={(e) => updateTicket(ticket.id, { priority: e.target.value as Priority })}
                className="block w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {priorityOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Story Points</label>
              <div className="rounded-md border border-input bg-background px-2 py-1 text-sm font-mono">
                {ticket.storyPoints}
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-6 space-y-6">
          {/* User Story */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-primary" />
              User Story
            </h3>
            <div className="rounded-lg border border-border bg-muted/30 p-4 text-sm leading-relaxed whitespace-pre-wrap">
              {ticket.userStory}
            </div>
          </div>

          {/* Acceptance Criteria */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <CheckSquare className="h-4 w-4 text-primary" />
              Acceptance Criteria
            </h3>
            <div className="space-y-1">
              {ticket.acceptanceCriteria.map((criterion, index) => (
                <button
                  key={index}
                  onClick={() => toggleCriteria(index)}
                  className="flex items-center gap-2 w-full text-left p-2 rounded-md hover:bg-accent/50 transition-colors"
                >
                  {checkedCriteria.has(index) ? (
                    <CheckSquare className="h-4 w-4 text-agent-active shrink-0" />
                  ) : (
                    <Square className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                  <span
                    className={cn('text-sm', checkedCriteria.has(index) && 'line-through text-muted-foreground')}
                  >
                    {criterion}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Technical Notes */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Code2 className="h-4 w-4 text-primary" />
              Technical Notes
            </h3>
            <div className="rounded-lg border border-border bg-muted/50 p-4 font-mono text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap">
              {ticket.technicalNotes}
            </div>
          </div>

          {/* Comments */}
          <CommentSection ticketId={ticket.id} />
        </div>
      </div>
    </div>
  );
}
