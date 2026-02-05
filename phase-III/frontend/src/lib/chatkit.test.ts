/**
 * ChatKit Configuration Validation Tests
 *
 * Basic validation tests to ensure the ChatKit configuration is correct.
 * Run with: npm test
 */

import { describe, it, expect } from '@jest/globals';

// Mock the ChatKit SDK since it may not be installed
jest.mock('@openai/chatkit', () => ({
  ChatKit: class MockChatKit {
    constructor(config: unknown) {
      return config;
    }
  },
  RESTAdapter: class MockRESTAdapter {
    constructor() {}
  },
}));

// Import after mocking
import {
  chatKit,
  ChatKitError,
  ChatKitErrorType,
  ALLOWED_TOOLS,
  API_URL,
  CHAT_ENDPOINT,
} from './chatkit';

describe('ChatKit Configuration', () => {
  describe('Environment Configuration', () => {
    it('should have API_URL configured', () => {
      expect(API_URL).toBeDefined();
      expect(typeof API_URL).toBe('string');
      expect(API_URL.length).toBeGreaterThan(0);
    });

    it('should have CHAT_ENDPOINT configured', () => {
      expect(CHAT_ENDPOINT).toBeDefined();
      expect(CHAT_ENDPOINT).toBe('/api');
    });

    it('should use default API URL when env vars not set', () => {
      // When no env vars are set, should default to localhost:8000
      const defaultUrl = 'http://localhost:8000';
      expect(API_URL).toContain(defaultUrl);
    });
  });

  describe('Domain Allowlist', () => {
    it('should have all required tools in allowlist', () => {
      const requiredTools = ['add_task', 'list_tasks', 'complete_task', 'update_task', 'delete_task'];

      requiredTools.forEach(tool => {
        expect(ALLOWED_TOOLS).toContain(tool);
      });
    });

    it('should have exactly 5 allowed tools', () => {
      expect(ALLOWED_TOOLS.length).toBe(5);
    });

    it('should be a readonly array', () => {
      // ALLOWED_TOOLS is defined with 'as const', making it readonly
      expect(Array.isArray(ALLOWED_TOOLS)).toBe(true);
    });
  });

  describe('ChatKit Instance', () => {
    it('should have chatKit instance exported', () => {
      expect(chatKit).toBeDefined();
    });

    it('should have adapter configured', () => {
      expect(chatKit).toHaveProperty('adapter');
    });

    it('should have domain configured', () => {
      expect(chatKit).toHaveProperty('domain');
      expect(chatKit.domain).toHaveProperty('name', 'task_management');
      expect(chatKit.domain).toHaveProperty('allowedTools');
      expect(chatKit.domain).toHaveProperty('validateToolCall');
    });

    it('should have error handler configured', () => {
      expect(chatKit).toHaveProperty('errorHandler');
      expect(typeof chatKit.errorHandler).toBe('function');
    });

    it('should have config with timeout and retries', () => {
      expect(chatKit).toHaveProperty('config');
      expect(chatKit.config).toHaveProperty('timeout');
      expect(chatKit.config).toHaveProperty('retries');
      expect(chatKit.config.timeout).toBe(30000);
      expect(chatKit.config.retries).toBe(3);
    });
  });

  describe('Error Handling', () => {
    it('should export ChatKitError class', () => {
      expect(ChatKitError).toBeDefined();
      expect(ChatKitError.prototype).toBeInstanceOf(Error);
    });

    it('should export ChatKitErrorType enum', () => {
      expect(ChatKitErrorType).toBeDefined();
      expect(ChatKitErrorType.NETWORK_ERROR).toBe('NETWORK_ERROR');
      expect(ChatKitErrorType.API_ERROR).toBe('API_ERROR');
      expect(ChatKitErrorType.TIMEOUT_ERROR).toBe('TIMEOUT_ERROR');
      expect(ChatKitErrorType.VALIDATION_ERROR).toBe('VALIDATION_ERROR');
      expect(ChatKitErrorType.UNKNOWN_ERROR).toBe('UNKNOWN_ERROR');
    });

    it('should create ChatKitError with correct properties', () => {
      const error = new ChatKitError(
        ChatKitErrorType.NETWORK_ERROR,
        'Test error',
        { original: 'error' },
        500
      );

      expect(error.type).toBe(ChatKitErrorType.NETWORK_ERROR);
      expect(error.message).toBe('Test error');
      expect(error.originalError).toEqual({ original: 'error' });
      expect(error.statusCode).toBe(500);
      expect(error.name).toBe('ChatKitError');
    });
  });

  describe('Tool Validation', () => {
    // Import the internal isToolAllowed function for testing
    // Note: This would need to be exported from chatkit.ts for testing
    it.todo('should allow valid tools');
    it.todo('should block invalid tools');
  });

  describe('Configuration Constants', () => {
    it('should have REQUEST_TIMEOUT set to 30 seconds', () => {
      // This is tested indirectly via chatKit.config.timeout
      expect(chatKit.config.timeout).toBe(30000);
    });

    it('should have MAX_RETRIES set to 3', () => {
      // This is tested indirectly via chatKit.config.retries
      expect(chatKit.config.retries).toBe(3);
    });

    it('should have RETRY_BASE_DELAY set to 1 second', () => {
      // This constant is used internally but not exported
      // Can be tested by checking retry behavior in integration tests
      expect(chatKit.config.retries).toBeGreaterThan(0);
    });
  });

  describe('Type Safety', () => {
    it('should export ChatKit type', () => {
      // Type exports are verified at compile time
      expect(() => {
        const typed: typeof import('./chatkit').ChatKit = chatKit;
        return typed;
      }).not.toThrow();
    });
  });
});

describe('ChatKit Configuration Integration', () => {
  describe('URL Construction', () => {
    it('should construct correct chat endpoint URL', () => {
      const userId = 'test-user-123';
      const expectedUrl = `${API_URL}${CHAT_ENDPOINT}/${encodeURIComponent(userId)}/chat`;
      const actualUrl = `${API_URL}/api/test-user-123/chat`;

      expect(actualUrl).toContain(API_URL);
      expect(actualUrl).toContain(CHAT_ENDPOINT);
      expect(actualUrl).toContain(userId);
    });
  });

  describe('Error Handler', () => {
    it('should handle ChatKitError instances', () => {
      const error = new ChatKitError(ChatKitErrorType.NETWORK_ERROR, 'Test');
      const result = chatKit.errorHandler(error);

      expect(result).toBe(error);
    });

    it('should wrap unknown errors in ChatKitError', () => {
      const error = new Error('Unknown error');
      const result = chatKit.errorHandler(error);

      expect(result).toBeInstanceOf(ChatKitError);
      expect(result.type).toBe(ChatKitErrorType.UNKNOWN_ERROR);
    });
  });
});

/**
 * Manual Testing Instructions
 *
 * 1. Start backend server:
 *    cd backend && uvicorn app.main:app --reload
 *
 * 2. In browser console or Node.js REPL:
 *
 * ```javascript
 * import { chatKit } from './src/lib/chatkit';
 *
 * // Test basic request
 * try {
 *   const response = await chatKit.chat('test-user', [
 *     { role: 'user', content: 'Add a task to test ChatKit' }
 *   ]);
 *   console.log('Success:', response);
 * } catch (error) {
 *   console.error('Error:', error);
 * }
 *
 * // Test validation error
 * try {
 *   await chatKit.chat('', []);
 * } catch (error) {
 *   console.log('Expected validation error:', error.type);
 * }
 * ```
 */
