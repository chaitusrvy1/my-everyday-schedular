
import { Task } from "../types";

const BASE_URL = '/api';

const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorText = await response.text();
    console.error(`API Error: ${errorText}`);
    throw new Error(`Sync failed: ${response.status}`);
  }
  return response.json();
};

export const apiService = {
  async getTasks(): Promise<Task[]> {
    try {
      const response = await fetch(`${BASE_URL}/tasks`);
      return await handleResponse(response);
    } catch (error) {
      console.warn("Backend unavailable, using local mode:", error);
      return [];
    }
  },

  async createTask(task: Omit<Task, 'id' | 'createdAt' | 'completed'>): Promise<Task> {
    const response = await fetch(`${BASE_URL}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task),
    });
    return await handleResponse(response);
  },

  async toggleTask(id: string): Promise<void> {
    const response = await fetch(`${BASE_URL}/tasks/${id}/toggle`, { method: 'PATCH' });
    await handleResponse(response);
  },

  async deleteTask(id: string): Promise<void> {
    const response = await fetch(`${BASE_URL}/tasks/${id}`, { method: 'DELETE' });
    await handleResponse(response);
  },

  async triggerManualBriefing(): Promise<void> {
    const response = await fetch(`${BASE_URL}/cron`);
    await handleResponse(response);
  },

  async getSettings(): Promise<{ email: string; name: string }> {
    const response = await fetch(`${BASE_URL}/settings`);
    return await handleResponse(response);
  },

  async saveSettings(settings: { email: string; name: string }): Promise<void> {
    const response = await fetch(`${BASE_URL}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    await handleResponse(response);
  }
};
