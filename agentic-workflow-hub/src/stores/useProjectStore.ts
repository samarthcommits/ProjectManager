import { create } from 'zustand';
import type { TeamMember, UploadedFile, AgentStep, Ticket, Comment, Phase, FileStatus } from '@/types/project';

const defaultTeam: TeamMember[] = [
  { id: '1', name: 'Alice', role: 'Backend Developer', skills: ['Python', 'Django', 'PostgreSQL'] },
  { id: '2', name: 'Bob', role: 'Frontend Developer', skills: ['React', 'TypeScript', 'Tailwind'] },
  { id: '3', name: 'Charlie', role: 'QA Engineer', skills: ['Selenium', 'Cypress', 'Jest'] },
];

interface ProjectState {
  projectBrief: string;
  setProjectBrief: (brief: string) => void;

  uploadedFiles: UploadedFile[];
  addFile: (file: UploadedFile) => void;
  removeFile: (id: string) => void;
  updateFileStatus: (id: string, status: FileStatus, progress?: number) => void;

  teamMembers: TeamMember[];
  addTeamMember: (member: TeamMember) => void;
  removeTeamMember: (id: string) => void;

  agentSteps: AgentStep[];
  setAgentSteps: (steps: AgentStep[]) => void;
  updateAgentStep: (id: string, updates: Partial<AgentStep>) => void;

  // --- ADD THESE 2 LINES ---
  baSummary: string;
  setBaSummary: (summary: string) => void;
  // -------------------------

  tickets: Ticket[];
  setTickets: (tickets: Ticket[]) => void;
  updateTicket: (id: string, updates: Partial<Ticket>) => void;
  deleteTicket: (id: string) => void;

  comments: Record<string, Comment[]>;
  addComment: (ticketId: string, comment: Comment) => void;

  currentPhase: Phase;
  setCurrentPhase: (phase: Phase) => void;

  sessionId: string | null;
  setSessionId: (id: string) => void;

  reset: () => void;
  
}

export const useProjectStore = create<ProjectState>((set) => ({
  projectBrief: '',
  setProjectBrief: (brief) => set({ projectBrief: brief }),

  uploadedFiles: [],
  addFile: (file) => set((s) => ({ uploadedFiles: [...s.uploadedFiles, file] })),
  removeFile: (id) => set((s) => ({ uploadedFiles: s.uploadedFiles.filter((f) => f.id !== id) })),
  updateFileStatus: (id, status, progress) =>
    set((s) => ({
      uploadedFiles: s.uploadedFiles.map((f) =>
        f.id === id ? { ...f, status, progress: progress ?? f.progress } : f
      ),
    })),

  teamMembers: defaultTeam,
  addTeamMember: (member) => set((s) => ({ teamMembers: [...s.teamMembers, member] })),
  removeTeamMember: (id) => set((s) => ({ teamMembers: s.teamMembers.filter((m) => m.id !== id) })),

  agentSteps: [],
  setAgentSteps: (steps) => set({ agentSteps: steps }),
  updateAgentStep: (id, updates) =>
    set((s) => ({
      agentSteps: s.agentSteps.map((step) => (step.id === id ? { ...step, ...updates } : step)),
    })),

  // --- ADD THIS IMPLEMENTATION ---
  baSummary: '',
  setBaSummary: (summary) => set({ baSummary: summary }),
  // -------------------------------
  
  tickets: [],
  setTickets: (tickets) => set({ tickets }),
  updateTicket: (id, updates) =>
    set((s) => ({
      tickets: s.tickets.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),
  deleteTicket: (id) => set((s) => ({ tickets: s.tickets.filter((t) => t.id !== id) })),

  comments: {},
  addComment: (ticketId, comment) =>
    set((s) => ({
      comments: {
        ...s.comments,
        [ticketId]: [...(s.comments[ticketId] || []), comment],
      },
    })),

  currentPhase: 'initiation',
  setCurrentPhase: (phase) => set({ currentPhase: phase }),
  sessionId: null,
  setSessionId: (id) => set({ sessionId: id }),
  reset: () =>
    set({
      projectBrief: '',
      uploadedFiles: [],
      teamMembers: defaultTeam,
      agentSteps: [],
      // Reset summary too
      baSummary: '', 
      tickets: [],
      comments: {},
      currentPhase: 'initiation',
    }),
}));