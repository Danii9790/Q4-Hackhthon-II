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
};

/**
 * Export the configured Axios instance for direct use if needed.
 */
export default apiClient;
