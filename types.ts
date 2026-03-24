
export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
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
