import { LayoutDashboard } from 'lucide-react';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';
import { useProjectStore } from '@/stores/useProjectStore';
import { cn } from '@/lib/utils';

const Dashboard = () => {
  const tickets = useProjectStore((s) => s.tickets);

  const stats = [
    { label: 'Total', value: tickets.length, color: 'text-foreground' },
    { label: 'Todo', value: tickets.filter((t) => t.status === 'todo').length, color: 'text-muted-foreground' },
    { label: 'Active', value: tickets.filter((t) => t.status === 'in-progress').length, color: 'text-primary' },
    { label: 'Review', value: tickets.filter((t) => t.status === 'in-review').length, color: 'text-status-medium' },
    { label: 'Done', value: tickets.filter((t) => t.status === 'done').length, color: 'text-agent-active' },
  ];

  return (
    <div className="mx-auto max-w-screen-2xl px-4 py-8 md:px-6 md:py-12 animate-fade-in">
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary mb-2">
            <LayoutDashboard className="h-3.5 w-3.5" />
            Sprint Board
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Project Dashboard</h1>
        </div>

        <div className="flex items-center gap-3">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center px-3">
              <p className={cn('text-xl font-bold', stat.color)}>{stat.value}</p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>

      <KanbanBoard />
    </div>
  );
};

export default Dashboard;
