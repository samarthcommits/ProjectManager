import { FileText } from 'lucide-react';
import { useProjectStore } from '@/stores/useProjectStore';

export function ProjectBrief() {
  const { projectBrief, setProjectBrief } = useProjectStore();

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <FileText className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Project Brief</h2>
      </div>
      <p className="text-sm text-muted-foreground">
        Describe the software you want to build. Be as detailed as possible about features, users, and technical requirements.
      </p>
      <textarea
        value={projectBrief}
        onChange={(e) => setProjectBrief(e.target.value)}
        placeholder="e.g., Build a SaaS platform for project management with real-time collaboration, Kanban boards, sprint planning, and automated reporting..."
        className="w-full min-h-[200px] rounded-lg border border-input bg-card p-4 text-sm placeholder:text-muted-foreground/60 resize-y focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background transition-shadow"
      />
      <div className="flex justify-end">
        <span className="text-xs text-muted-foreground">{projectBrief.length} characters</span>
      </div>
    </div>
  );
}
