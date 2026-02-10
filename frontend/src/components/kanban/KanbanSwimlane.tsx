import { TicketCard } from './TicketCard';
import type { Ticket, TicketStatus } from '@/types/project';

interface KanbanSwimlaneProps {
  assignee: string;
  tickets: Ticket[];
  statusColumns: { key: TicketStatus; label: string }[];
}

export function KanbanSwimlane({ assignee, tickets, statusColumns }: KanbanSwimlaneProps) {
  return (
    <div className="grid grid-cols-[140px_repeat(4,minmax(180px,1fr))] gap-3">
      {/* Assignee label */}
      <div className="flex items-start gap-2.5 pt-2 pr-2">
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-semibold text-primary shrink-0">
          {assignee.charAt(0)}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{assignee}</p>
          <p className="text-xs text-muted-foreground">{tickets.length} tickets</p>
        </div>
      </div>

      {/* Status columns */}
      {statusColumns.map((col) => {
        const columnTickets = tickets.filter((t) => t.status === col.key);
        return (
          <div key={col.key} className="space-y-2 min-h-[80px] rounded-lg bg-muted/30 p-2">
            {columnTickets.map((ticket) => (
              <TicketCard key={ticket.id} ticket={ticket} />
            ))}
            {columnTickets.length === 0 && (
              <div className="h-full min-h-[60px] flex items-center justify-center">
                <span className="text-xs text-muted-foreground/30">—</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
