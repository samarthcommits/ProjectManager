import { useLocation, useNavigate } from 'react-router-dom';
import { Bot, LayoutDashboard, ListChecks, Rocket } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { cn } from '@/lib/utils';
import { useProjectStore } from '@/stores/useProjectStore';

const navItems = [
  { label: 'Initiation', path: '/', icon: Rocket, phase: 'initiation' as const },
  { label: 'Processing', path: '/processing', icon: Bot, phase: 'processing' as const },
  { label: 'Review', path: '/review', icon: ListChecks, phase: 'review' as const },
  { label: 'Board', path: '/dashboard', icon: LayoutDashboard, phase: 'dashboard' as const },
];

const phaseOrder = ['initiation', 'processing', 'review', 'dashboard'];

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPhase = useProjectStore((s) => s.currentPhase);
  const currentPhaseIndex = phaseOrder.indexOf(currentPhase);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-screen-2xl items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-2">
          <Bot className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">AgentPM</span>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item, index) => {
            const isActive = location.pathname === item.path;
            const isAccessible = index <= currentPhaseIndex;

            return (
              <button
                key={item.path}
                onClick={() => isAccessible && navigate(item.path)}
                disabled={!isAccessible}
                className={cn(
                  'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : isAccessible
                    ? 'text-muted-foreground hover:text-foreground hover:bg-accent'
                    : 'text-muted-foreground/40 cursor-not-allowed'
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <ThemeToggle />
      </div>
    </header>
  );
}
