import { useState } from 'react';
import { cn } from '@/lib/utils';
import { TicketDetailModal } from './TicketDetailModal';
import type { Ticket, Priority } from '@/types/project';

const priorityConfig: Record<Priority, { label: string; dotColor: string; bgColor: string }> = {
  critical: { label: 'Critical', dotColor: 'bg-status-critical', bgColor: 'bg-status-critical/10' },
  high: { label: 'High', dotColor: 'bg-status-high', bgColor: 'bg-status-high/10' },
  medium: { label: 'Medium', dotColor: 'bg-status-medium', bgColor: 'bg-status-medium/10' },
  low: { label: 'Low', dotColor: 'bg-status-low', bgColor: 'bg-status-low/10' },
};

interface TicketCardProps {
  ticket: Ticket;
}

export function TicketCard({ ticket }: TicketCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const config = priorityConfig[ticket.priority];

  return (
    <>
      <div
        onClick={() => setIsOpen(true)}
        className="group cursor-pointer rounded-lg border border-border bg-card p-3 transition-all hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5 hover:border-primary/20"
      >
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="text-[10px] font-mono text-muted-foreground">{ticket.ticketId}</span>
          <div
            className={cn(
              'flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium',
              config.bgColor
            )}
          >
            <span className={cn('h-1.5 w-1.5 rounded-full', config.dotColor)} />
            {config.label}
          </div>
        </div>
        <p className="text-sm font-medium leading-snug line-clamp-2">{ticket.title}</p>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground bg-muted rounded px-1.5 py-0.5">{ticket.module}</span>
          <span className="text-[10px] font-mono text-muted-foreground bg-muted rounded px-1.5 py-0.5">
            {ticket.storyPoints} SP
          </span>
        </div>
      </div>
      <TicketDetailModal ticket={ticket} open={isOpen} onOpenChange={setIsOpen} />
    </>
  );
}
