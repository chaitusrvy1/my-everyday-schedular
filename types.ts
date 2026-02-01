
export enum TaskPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH'
}

export interface Task {
  id: string;
  title: string;
  description: string;
  date: string; // ISO format
  completed: boolean;
  priority: TaskPriority;
  createdAt: number;
}

export interface MorningBriefing {
  quote: string;
  author: string;
  message: string;
  actionItems: string[];
  generatedAt: number;
}

export interface UserSettings {
  email: string;
  preferredMorningTime: string; // HH:mm
  backendUrl?: string;
  brevoApiKey?: string;
  supabaseUrl?: string;
}
