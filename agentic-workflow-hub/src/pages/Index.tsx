import { useNavigate } from 'react-router-dom';
import { Rocket, ArrowRight } from 'lucide-react';
import { ProjectBrief } from '@/components/initiation/ProjectBrief';
import { FileUploader } from '@/components/initiation/FileUploader';
import { TeamRoster } from '@/components/initiation/TeamRoster';
import { useProjectStore } from '@/stores/useProjectStore';
import { Button } from '@/components/ui/button';

const Index = () => {
  const navigate = useNavigate();
  const { projectBrief, uploadedFiles, setCurrentPhase } = useProjectStore();

  const allFilesReady = uploadedFiles.length === 0 || uploadedFiles.every((f) => f.status === 'complete');
  const canGenerate = projectBrief.trim().length > 10 && allFilesReady;

  const handleGenerate = () => {
    setCurrentPhase('processing');
    navigate('/processing');
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:px-6 md:py-12 animate-fade-in">
      <div className="mb-8 text-center">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary mb-4">
          <Rocket className="h-3.5 w-3.5" />
          New Project
        </div>
        <h1 className="text-3xl font-bold tracking-tight md:text-4xl">Project Initiation</h1>
        <p className="mt-2 text-muted-foreground max-w-2xl mx-auto">
          Describe your software, upload relevant documents, and configure your team. Our AI agents will analyze
          everything and generate a complete project plan.
        </p>
      </div>

      <div className="space-y-8">
        <ProjectBrief />

        <div className="grid gap-8 md:grid-cols-2">
          <FileUploader />
          <TeamRoster />
        </div>

        <div className="flex justify-center pt-4">
          <Button onClick={handleGenerate} disabled={!canGenerate} size="lg" className="gap-2 text-base px-8 font-semibold">
            Generate Plan
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Index;
