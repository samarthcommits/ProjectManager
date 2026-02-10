import { useEffect, useRef } from 'react';
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';
import { useProjectStore } from '@/stores/useProjectStore';
import { cn } from '@/lib/utils';
import type { AgentStepStatus } from '@/types/project';

const statusConfig: Record<AgentStepStatus, { icon: React.ElementType; className: string }> = {
  pending: { icon: Circle, className: 'text-muted-foreground/40' },
  active: { icon: Loader2, className: 'text-primary animate-spin' },
  complete: { icon: CheckCircle2, className: 'text-agent-active' },
  error: { icon: AlertCircle, className: 'text-destructive' },
};

export function AgentTimeline() {
  const agentSteps = useProjectStore((s) => s.agentSteps);
  const activeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [agentSteps]);

  const completedCount = agentSteps.filter((s) => s.status === 'complete').length;
  const progress = agentSteps.length > 0 ? (completedCount / agentSteps.length) * 100 : 0;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Agent Progress</span>
          <span className="font-medium">
            {completedCount}/{agentSteps.length} steps
          </span>
        </div>
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="relative space-y-0">
        {agentSteps.map((step, index) => {
          const config = statusConfig[step.status];
          const Icon = config.icon;
          const isLast = index === agentSteps.length - 1;

          return (
            <div
              key={step.id}
              ref={step.status === 'active' ? activeRef : undefined}
              className="relative flex gap-4 pb-6"
            >
              {/* Timeline connector */}
              {!isLast && (
                <div className="absolute left-[15px] top-[32px] h-[calc(100%-20px)] w-px">
                  <div
                    className={cn(
                      'h-full w-full transition-colors duration-500',
                      step.status === 'complete' ? 'bg-agent-active' : 'bg-border'
                    )}
                  />
                </div>
              )}

              {/* Icon node */}
              <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-card">
                <Icon className={cn('h-4 w-4', config.className)} />
              </div>

              {/* Content */}
              <div
                className={cn(
                  'flex-1 pt-0.5 transition-opacity duration-300',
                  step.status === 'pending' ? 'opacity-40' : 'opacity-100'
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="text-base">{step.emoji}</span>
                  <span className="text-sm font-semibold">{step.agent}</span>
                  {step.status === 'active' && (
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
                    </span>
                  )}
                </div>
                <p
                  className={cn(
                    'text-sm mt-0.5',
                    step.status === 'active' ? 'text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {step.message}
                </p>
                {step.detail && (
                  <p className="text-xs text-muted-foreground mt-1 font-mono bg-muted/50 rounded px-2 py-1 inline-block">
                    {step.detail}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
