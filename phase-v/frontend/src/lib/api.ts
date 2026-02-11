/**
 * Axios API client for Todo Application.
 *
 * This module provides a typed HTTP client for communicating with the backend API.
 * It automatically includes JWT tokens from authentication session and handles 401 errors.
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

import type {
  Task,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskListResponse,
} from '@/types/task';
import type { ChatRequest, ChatResponse } from '@/types/chat';
import { getAuthToken, getCurrentUser, clearSession } from '@/lib/auth';

/**
 * Create configured Axios instance with base URL from environment.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to attach JWT token from session.
 *
 * This interceptor runs before every request and adds the Authorization header
 * with the Bearer token stored by the auth utilities.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from auth utilities (stored by login/signup flows)
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle 401 errors.
 *
 * When a 401 Unauthorized response is received, this interceptor:
 * - Clears the invalid session data using auth utilities
 * - Redirects to the login page
 *
 * This can happen when:
 * - Token is expired
 * - Token is invalid
 * - User is not authenticated
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear the invalid session data using auth utilities
      clearSession();

      // Redirect to login if not already there
      if (typeof window !== 'undefined') {
        const currentPath = window.location.pathname;
        if (currentPath !== '/login') {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Get the current user ID from session.
 *
 * @returns User ID or null if not found
 */
function getCurrentUserId(): string | null {
  const user = getCurrentUser();
  return user?.id || null;
}

/**
 * Chat API methods.
 */
export const chatApi = {
  /**
   * Send a chat message and get AI response.
   *
   * POST /api/users/{userId}/chat
   *
   * @param message - User's message text
   * @returns AI response with tool calls if any
   */
  async sendMessage(message: string): Promise<ChatResponse> {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('User not authenticated');
    }

    const response = await apiClient.post<ChatResponse>(
      `/users/${userId}/chat`,
      { message } as ChatRequest
    );
    return response.data;
  },
};

/**
 * Task API methods.
 */
export const taskApi = {
  /**
   * Get all tasks for the authenticated user.
   *
   * GET /api/users/{userId}/tasks
   *
   * @param offset - Number of tasks to skip (for pagination)
   * @param limit - Maximum number of tasks to return
   * @returns Paginated list of tasks
   */
  async getTasks(offset: number = 0, limit: number = 50): Promise<TaskListResponse> {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('User not authenticated');
    }

    const response = await apiClient.get<TaskListResponse>(`/users/${userId}/tasks`, {
      params: { offset, limit },
    });
    return response.data;
  },

  /**
   * Get a single task by ID.
   *
   * GET /api/users/{userId}/tasks/{id}
   *
   * @param id - Task ID
   * @returns Task details
   */
  async getTask(id: number): Promise<Task> {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('User not authenticated');
    }

    const response = await apiClient.get<Task>(`/users/${userId}/tasks/${id}`);
    return response.data;
  },

  /**
   * Create a new task.
   *
   * POST /api/users/{userId}/tasks
   *
   * @param data - Task creation request
   * @returns Created task with generated ID
   */
  async createTask(data: TaskCreateRequest): Promise<Task> {
    const userId = getCurrentUserId();
    if (!userId) {
      throw new Error('User not authenticated');
    }

    const response = await apiClient.post<Task>(`/users/${userId}/tasks`, data);
    return response.data;
  },

  /**
   * Update an existing task.
   *
   * PATCH /api/tasks/{id}
   *
   * @param id - Task ID
   * @param data - Task update request
   * @returns Updated task
   */
  async updateTask(id: number, data: TaskUpdateRequest): Promise<Task> {
    const response = await apiClient.patch<Task>(`/tasks/${id}`, data);
    return response.data;
  },

  /**
   * Mark a task as completed.
   *
   * PATCH /api/tasks/{id}/complete
   *
   * @param id - Task ID
   * @returns Updated task with completed=true
   */
  async completeTask(id: number): Promise<Task> {
    const response = await apiClient.patch<Task>(`/tasks/${id}/complete`);
    return response.data;
  },

  /**
   * Mark a task as incomplete (uncomplete).
   *
   * PATCH /api/tasks/{id}/uncomplete
   *
   * @param id - Task ID
   * @returns Updated task with completed=false
   */
  async uncompleteTask(id: number): Promise<Task> {
    const response = await apiClient.patch<Task>(`/tasks/${id}/uncomplete`);
    return response.data;
  },

  /**
   * Delete a task.
   *
   * DELETE /api/tasks/{id}
   *
   * @param id - Task ID
   */
  async deleteTask(id: number): Promise<void> {
    await apiClient.delete(`/tasks/${id}`);
  },

  // ========================================================================
  // Phase V: Advanced Task Management API Methods
  // ========================================================================

  /**
   * T051: Get filtered/sorted tasks with advanced options.
   *
   * GET /api/tasks (with query params)
   *
   * @param filters - Filter and sort options
   * @returns Paginated list of filtered/sorted tasks
   */
  async filterTasks(filters: {
    priority?: 'LOW' | 'MEDIUM' | 'HIGH'
    tags?: string[]
    dueBefore?: string
    dueAfter?: string
    search?: string
    sortBy?: 'created_at' | 'updated_at' | 'due_date' | 'priority'
    sortOrder?: 'asc' | 'desc'
    offset?: number
    limit?: number
  } = {}): Promise<TaskListResponse> {
    const params: Record<string, string | string[] | number> = {
      offset: filters.offset || 0,
      limit: filters.limit || 50,
    }

    if (filters.priority) params.priority = filters.priority
    if (filters.tags && filters.tags.length > 0) params.tags = filters.tags.join(',')
    if (filters.dueBefore) params.due_before = filters.dueBefore
    if (filters.dueAfter) params.due_after = filters.dueAfter
    if (filters.search) params.search = filters.search
    if (filters.sortBy) params.sort_by = filters.sortBy
    if (filters.sortOrder) params.sort_order = filters.sortOrder

    const response = await apiClient.get<TaskListResponse>('/tasks', { params })
    return response.data
  },

  /**
   * T051: Sort tasks by specified field and order.
   *
   * @param sortBy - Field to sort by
   * @param sortOrder - Sort direction
   * @returns Sorted tasks
   */
  async sortTasks(
    sortBy: 'created_at' | 'updated_at' | 'due_date' | 'priority' = 'created_at',
    sortOrder: 'asc' | 'desc' = 'desc',
    offset: number = 0,
    limit: number = 50
  ): Promise<TaskListResponse> {
    return this.filterTasks({ sortBy, sortOrder, offset, limit })
  },

  /**
   * T051: Search tasks by query string.
   *
   * @param query - Search query for title/description
   * @returns Matching tasks
   */
  async searchTasks(query: string, offset: number = 0, limit: number = 50): Promise<TaskListResponse> {
    return this.filterTasks({ search: query, offset, limit })
  },

  /**
   * Set task priority.
   *
   * PATCH /api/tasks/{id}/priority
   *
   * @param id - Task ID
   * @param priority - New priority value
   * @returns Updated task
   */
  async setTaskPriority(id: number, priority: 'LOW' | 'MEDIUM' | 'HIGH'): Promise<Task> {
    const response = await apiClient.patch<Task>(`/tasks/${id}/priority`, { priority })
    return response.data
  },

  /**
   * Set task due date.
   *
   * PATCH /api/tasks/{id}/due-date
   *
   * @param id - Task ID
   * @param dueDate - New due date (ISO string) or null to remove
   * @returns Updated task
   */
  async setTaskDueDate(id: number, dueDate: string | null): Promise<Task> {
    const response = await apiClient.patch<Task>(`/tasks/${id}/due-date`, { due_date: dueDate })
    return response.data
  },

  /**
   * Add tags to a task.
   *
   * POST /api/tasks/{id}/tags
   *
   * @param id - Task ID
   * @param tags - Tags to add
   * @returns Updated task
   */
  async addTaskTags(id: number, tags: string[]): Promise<Task> {
    const response = await apiClient.post<Task>(`/tasks/${id}/tags`, { tags })
    return response.data
  },
};

/**
 * Export the configured Axios instance for direct use if needed.
 */
export default apiClient;
