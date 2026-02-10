export type Priority = 'critical' | 'high' | 'medium' | 'low';
export type TicketStatus = 'todo' | 'in-progress' | 'in-review' | 'done';
export type FileStatus = 'uploading' | 'parsing' | 'vectorizing' | 'complete' | 'error';
export type AgentStepStatus = 'pending' | 'active' | 'complete' | 'error';
export type Phase = 'initiation' | 'processing' | 'review' | 'dashboard';

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  skills: string[];
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: FileStatus;
  progress: number;
}

export interface AgentStep {
  id: string;
  agent: string;
  emoji: string;
  message: string;
  status: AgentStepStatus;
  detail?: string;
  timestamp?: Date;
}

export interface Ticket {
  id: string;
  ticketId: string;
  module: string;
  title: string;
  priority: Priority;
  status: TicketStatus;
  assignee: string;
  storyPoints: number;
  userStory: string;
  acceptanceCriteria: string[];
  technicalNotes: string;
}

export interface Comment {
  id: string;
  author: string;
  content: string;
  timestamp: Date;
}
