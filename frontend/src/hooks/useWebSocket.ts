import { useEffect, useCallback, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface UseWebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
  onMessage?: (message: WebSocketMessage) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  autoConnect?: boolean;
}

export interface UseWebSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastMessage: WebSocketMessage | null;
  connect: () => void;
  disconnect: () => void;
  subscribe: (event: string, callback: (data: any) => void) => () => void;
  emit: (event: string, data: any) => void;
  reconnect: () => void;
}

export const useWebSocket = (
  url?: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    onConnect,
    onDisconnect,
    onError,
    onMessage,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    autoConnect = true
  } = options;

  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const socketRef = useRef<Socket | null>(null);

  // Get WebSocket URL from environment or use provided URL
  const wsUrl = url || process.env.REACT_APP_WS_URL || 'http://localhost:8000';

  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const token = localStorage.getItem('auth_token');
      const socketOptions = {
        transports: ['websocket', 'polling'],
        auth: token ? { token } : {},
        forceNew: true,
        reconnection: true,
        reconnectionDelay: reconnectInterval,
        reconnectionAttempts: maxReconnectAttempts,
      };

      const newSocket = io(wsUrl, socketOptions);
      socketRef.current = newSocket;
      setSocket(newSocket);

      // Connection event handlers
      newSocket.on('connect', () => {
        console.log('WebSocket connected to:', wsUrl);
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        onConnect?.();
      });

      newSocket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        onDisconnect?.();

        // Auto-reconnect logic
        if (reason === 'io server disconnect') {
          // Server initiated disconnect, don't reconnect automatically
          return;
        }

        if (reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      });

      newSocket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        setConnectionStatus('error');
        onError?.(error);

        // Retry connection
        if (reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      });

      // Listen for all incoming messages
      newSocket.onAny((eventName, data) => {
        const message: WebSocketMessage = {
          type: eventName,
          data,
          timestamp: new Date().toISOString()
        };
        setLastMessage(message);
        onMessage?.(message);
      });

      // Real-time emission updates
      newSocket.on('emissions_updated', (data) => {
        console.log('Emissions updated:', data);
      });

      newSocket.on('dashboard_update', (data) => {
        console.log('Dashboard update received:', data);
      });

      newSocket.on('data_quality_alert', (data) => {
        console.log('Data quality alert:', data);
      });

      newSocket.on('sync_status', (data) => {
        console.log('Sync status update:', data);
      });

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
      onError?.(error);
    }
  }, [wsUrl, onConnect, onDisconnect, onError, onMessage, reconnectInterval, maxReconnectAttempts, reconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setSocket(null);
      setIsConnected(false);
      setConnectionStatus('disconnected');
      setReconnectAttempts(0);
    }
  }, []);

  const subscribe = useCallback((event: string, callback: (data: any) => void) => {
    if (!socketRef.current) {
      console.warn('WebSocket not connected. Cannot subscribe to event:', event);
      return () => {};
    }

    socketRef.current.on(event, callback);

    // Return unsubscribe function
    return () => {
      if (socketRef.current) {
        socketRef.current.off(event, callback);
      }
    };
  }, []);

  const emit = useCallback((event: string, data: any) => {
    if (!socketRef.current?.connected) {
      console.warn('WebSocket not connected. Cannot emit event:', event);
      return;
    }

    socketRef.current.emit(event, data);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    setReconnectAttempts(0);
    setTimeout(() => {
      connect();
    }, 1000);
  }, [disconnect, connect]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect && wsUrl) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, wsUrl, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    socket: socketRef.current,
    isConnected,
    connectionStatus,
    lastMessage,
    connect,
    disconnect,
    subscribe,
    emit,
    reconnect,
  };
};

export default useWebSocket;
