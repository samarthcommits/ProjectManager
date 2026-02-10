import { useCallback, useState } from 'react';
import { Upload, File, CheckCircle2, Loader2, X, FileText } from 'lucide-react';
import { useProjectStore } from '@/stores/useProjectStore';
import { cn } from '@/lib/utils';
import type { UploadedFile, FileStatus } from '@/types/project';

const statusLabels: Record<FileStatus, string> = {
  uploading: 'Uploading...',
  parsing: 'Parsing PDF...',
  vectorizing: 'Vectorizing...',
  complete: 'Ready',
  error: 'Error',
};

export function FileUploader() {
  const { uploadedFiles, addFile, removeFile, updateFileStatus } = useProjectStore();
  const [isDragging, setIsDragging] = useState(false);

  const simulateProcessing = useCallback(
    (fileId: string) => {
      const stages: { status: FileStatus; delay: number }[] = [
        { status: 'uploading', delay: 0 },
        { status: 'parsing', delay: 800 },
        { status: 'vectorizing', delay: 2000 },
        { status: 'complete', delay: 3500 },
      ];
      stages.forEach(({ status, delay }) => {
        setTimeout(() => updateFileStatus(fileId, status, status === 'complete' ? 100 : 50), delay);
      });
    },
    [updateFileStatus]
  );

  const handleFiles = useCallback(
    (files: FileList) => {
      Array.from(files).forEach((file) => {
        const id = `file-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const uploaded: UploadedFile = {
          id,
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'uploading',
          progress: 0,
        };
        addFile(uploaded);
        simulateProcessing(id);
      });
    },
    [addFile, simulateProcessing]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const openFilePicker = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.pdf,.docx,.doc';
    input.onchange = (e) => {
      const files = (e.target as HTMLInputElement).files;
      if (files) handleFiles(files);
    };
    input.click();
  };

  const statusIcon = (status: FileStatus) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      case 'parsing':
        return <Loader2 className="h-4 w-4 animate-spin text-status-medium" />;
      case 'vectorizing':
        return <Loader2 className="h-4 w-4 animate-spin text-status-high" />;
      case 'complete':
        return <CheckCircle2 className="h-4 w-4 text-agent-active" />;
      case 'error':
        return <X className="h-4 w-4 text-destructive" />;
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Upload className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Document Ingestion</h2>
      </div>
      <p className="text-sm text-muted-foreground">
        Upload PRDs, specs, or design docs (PDF/Docx). Files will be parsed and vectorized for AI processing.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={openFilePicker}
        className={cn(
          'flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 cursor-pointer transition-all',
          isDragging
            ? 'border-primary bg-primary/5 scale-[1.02]'
            : 'border-border hover:border-muted-foreground/30 hover:bg-accent/50'
        )}
      >
        <div className="rounded-full bg-primary/10 p-3">
          <FileText className="h-6 w-6 text-primary" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium">Drop files here or click to browse</p>
          <p className="text-xs text-muted-foreground mt-1">PDF, DOCX up to 50MB</p>
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          {uploadedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-3 rounded-lg border border-border bg-card p-3 animate-fade-in"
            >
              <File className="h-4 w-4 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(file.size / 1024).toFixed(1)} KB · {statusLabels[file.status]}
                </p>
              </div>
              {statusIcon(file.status)}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(file.id);
                }}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
