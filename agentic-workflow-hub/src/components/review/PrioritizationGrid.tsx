import { Trash2 } from 'lucide-react';
import { useProjectStore } from '@/stores/useProjectStore';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Priority } from '@/types/project';

const priorityConfig: Record<Priority, { label: string; className: string }> = {
  critical: { label: 'Critical', className: 'bg-status-critical/15 text-status-critical border-status-critical/30' },
  high: { label: 'High', className: 'bg-status-high/15 text-status-high border-status-high/30' },
  medium: { label: 'Medium', className: 'bg-status-medium/15 text-status-medium border-status-medium/30' },
  low: { label: 'Low', className: 'bg-status-low/15 text-status-low border-status-low/30' },
};

interface PrioritizationGridProps {
  onApprove: () => void;
}

export function PrioritizationGrid({ onApprove }: PrioritizationGridProps) {
  const { tickets, updateTicket, deleteTicket } = useProjectStore();

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left font-semibold px-4 py-3 text-muted-foreground">ID</th>
                <th className="text-left font-semibold px-4 py-3 text-muted-foreground">Module</th>
                <th className="text-left font-semibold px-4 py-3 text-muted-foreground">Assignee</th>
                <th className="text-left font-semibold px-4 py-3 text-muted-foreground">Title</th>
                <th className="text-left font-semibold px-4 py-3 text-muted-foreground">Priority</th>
                <th className="text-left font-semibold px-4 py-3 text-muted-foreground">SP</th>
                <th className="text-right font-semibold px-4 py-3 text-muted-foreground" />
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => {
                const config = priorityConfig[ticket.priority];
                return (
                  <tr
                    key={ticket.id}
                    className="border-b border-border last:border-0 hover:bg-accent/50 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{ticket.ticketId}</td>
                    <td className="px-4 py-3 text-muted-foreground">{ticket.module}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-semibold text-primary">
                          {ticket.assignee.charAt(0)}
                        </div>
                        <span>{ticket.assignee}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-medium max-w-[300px] truncate">{ticket.title}</td>
                    <td className="px-4 py-3">
                      <select
                        value={ticket.priority}
                        onChange={(e) => updateTicket(ticket.id, { priority: e.target.value as Priority })}
                        className={cn(
                          'rounded-full border px-2.5 py-0.5 text-xs font-semibold cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring',
                          config.className
                        )}
                      >
                        {Object.entries(priorityConfig).map(([key, val]) => (
                          <option key={key} value={key}>
                            {val.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3 text-center font-mono text-sm">{ticket.storyPoints}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => deleteTicket(ticket.id)}
                        className="text-muted-foreground hover:text-destructive transition-colors p-1 rounded"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {tickets.length} tickets · {tickets.reduce((sum, t) => sum + t.storyPoints, 0)} total story points
        </p>
        <Button onClick={onApprove} size="lg" className="font-semibold">
          Approve & Allocate →
        </Button>
      </div>
    </div>
  );
}
