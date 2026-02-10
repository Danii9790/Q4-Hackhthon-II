/**
 * Kafka WebSocket Client for Real-Time Task Updates
 *
 * T097-T098: Connects to WebSocket gateway and receives task updates.
 * Automatically updates local state when task updates received.
 *
 * Features:
 * - Automatic reconnection on disconnect
 * - Connection status tracking
 * - Task update event handling
 * - Graceful shutdown
 */

interface TaskUpdateMessage {
  type: 'task_created' | 'task_updated' | 'task_completed' | 'task_deleted'
  task_id: number
  data: {
    id: number
    user_id: string
    title: string
    description?: string
    completed: boolean
    completed_at?: string
    due_date?: string
    priority?: string
    tags?: string[]
    created_at: string
    updated_at: string
  }
  timestamp: string
}

type TaskUpdateHandler = (message: TaskUpdateMessage) => void
type ConnectionStatusHandler = (connected: boolean) => void

class KafkaWebSocketClient {
  private ws: WebSocket | null = null
  private reconnectTimeout: NodeJS.Timeout | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // Start with 1 second

  private userId: string | null = null
  private updateHandlers: Set<TaskUpdateHandler> = new Set()
  private statusHandlers: Set<ConnectionStatusHandler> = new Set()
  private isConnected = false

  /**
   * T097: Connect to WebSocket gateway.
   *
   * @param userId - User ID to connect as
   */
  connect(userId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected')
      return
    }

    this.userId = userId

    // Construct WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/users/${userId}/ws`

    console.log(`Connecting to WebSocket: ${wsUrl}`)

    try {
      this.ws = new WebSocket(wsUrl)

      // Connection opened
      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.isConnected = true
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000

        // Notify status handlers
        this.statusHandlers.forEach(handler => handler(true))

        // Start ping/pong to keep connection alive
        this.startPingPong()
      }

      // Message received
      this.ws.onmessage = (event) => {
        try {
          const message: TaskUpdateMessage = JSON.parse(event.data)

          // Handle ping/pong
          if (message.type === 'pong') {
            return
          }

          // Handle task updates
          console.log('Task update received:', message)

          // T098: Call update handlers
          this.updateHandlers.forEach(handler => handler(message))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      // Connection closed
      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        this.isConnected = false

        // Notify status handlers
        this.statusHandlers.forEach(handler => handler(false))

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        } else {
          console.error('Max reconnect attempts reached')
        }
      }

      // Connection error
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from WebSocket gateway.
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.isConnected = false
    this.userId = null
  }

  /**
   * T097: Subscribe to task updates.
   *
   * @param handler - Function to call when task update received
   * @returns Unsubscribe function
   */
  onTaskUpdate(handler: TaskUpdateHandler): () => void {
    this.updateHandlers.add(handler)

    // Return unsubscribe function
    return () => {
      this.updateHandlers.delete(handler)
    }
  }

  /**
   * Subscribe to connection status changes.
   *
   * @param handler - Function to call when connection status changes
   * @returns Unsubscribe function
   */
  onConnectionStatusChange(handler: ConnectionStatusHandler): () => void {
    this.statusHandlers.add(handler)

    // Return unsubscribe function
    return () => {
      this.statusHandlers.delete(handler)
    }
  }

  /**
   * Check if currently connected.
   */
  getConnectionStatus(): boolean {
    return this.isConnected
  }

  /**
   * Schedule reconnection attempt.
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      return // Already scheduled
    }

    this.reconnectAttempts++
    console.log(
      `Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} ` +
      `in ${this.reconnectDelay}ms`
    )

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null

      if (this.userId) {
        this.connect(this.userId)
      }

      // Exponential backoff
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000)
    }, this.reconnectDelay)
  }

  /**
   * Start ping/pong to keep connection alive.
   */
  private startPingPong(): void {
    // Send ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      } else {
        clearInterval(pingInterval)
      }
    }, 30000)
  }
}

// Global singleton instance
let kafkaClient: KafkaWebSocketClient | null = null

/**
 * Get or create the global Kafka WebSocket client instance.
 */
export function getKafkaClient(): KafkaWebSocketClient {
  if (!kafkaClient) {
    kafkaClient = new KafkaWebSocketClient()
  }
  return kafkaClient
}

/**
 * Initialize Kafka WebSocket client with user authentication.
 *
 * @param userId - Authenticated user ID
 */
export function initializeKafkaClient(userId: string): void {
  const client = getKafkaClient()
  client.connect(userId)
}

/**
 * Disconnect Kafka WebSocket client.
 */
export function disconnectKafkaClient(): void {
  if (kafkaClient) {
    kafkaClient.disconnect()
  }
}

export type { TaskUpdateMessage, TaskUpdateHandler }
