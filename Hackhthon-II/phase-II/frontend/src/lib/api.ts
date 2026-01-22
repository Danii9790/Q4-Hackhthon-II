/**
 * Axios API client for Todo Application.
 *
 * This module provides a typed HTTP client for communicating with the backend API.
 * It automatically includes JWT tokens from Better Auth session and handles 401 errors.
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

import type {
  Task,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskListResponse,
} from '@/types/task';

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
 * Request interceptor to attach JWT token from localStorage.
 *
 * This interceptor runs before every request and adds the Authorization header
 * with the Bearer token stored in localStorage after login/signup.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage (stored by login/signup forms)
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
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
 * - Clears the invalid token from localStorage
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
      // Clear the invalid session data from localStorage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');

        // Redirect to login if not already there
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
 * Get the current user ID from localStorage.
 *
 * @returns User ID or null if not found
 */
function getCurrentUserId(): string | null {
  if (typeof window === 'undefined') return null;

  try {
    const userData = localStorage.getItem('user_data');
    if (!userData) return null;

    const user = JSON.parse(userData);
    return user?.id || null;
  } catch (error) {
    console.error('Failed to get user ID from localStorage:', error);
    return null;
  }
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
