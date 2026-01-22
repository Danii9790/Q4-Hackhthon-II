/**
 * TypeScript types for Todo Application.
 */

/**
 * Task entity representing a single to-do item.
 */
export interface Task {
  id: number;
  user_id: string;
  title: string;
  description: string | null;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Request payload for creating a new task.
 */
export interface TaskCreateRequest {
  title: string;
  description?: string;
}

/**
 * Request payload for updating an existing task.
 */
export interface TaskUpdateRequest {
  title?: string;
  description?: string;
}

/**
 * Paginated task list response.
 */
export interface TaskListResponse {
  tasks: Task[];
  total: number;
  offset: number;
  limit: number;
}
