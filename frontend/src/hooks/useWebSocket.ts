import { useEffect, useCallback, useRef } from 'react';
import webSocketService from '../services/websocket';

interface UseWebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { onConnect, onDisconnect, onError } = options;
  const isConnectedRef = useRef(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    webSocketService.connect(token);

    webSocketService.on('connect', () => {
      isConnectedRef.current = true;
      onConnect?.();
    });

    webSocketService.on('disconnect', () => {
      isConnectedRef.current = false;
      onDisconnect?.();
    });

    webSocketService.on('error', (error) => {
      onError?.(error);
    });

    return () => {
      webSocketService.disconnect();
    };
  }, [onConnect, onDisconnect, onError]);

  const subscribe = useCallback((event: string, callback: (data: any) => void) => {
    webSocketService.on(event, callback);
    
    return () => {
      webSocketService.off(event);
    };
  }, []);

  const emit = useCallback((event: string, data: any) => {
    webSocketService.emit(event, data);
  }, []);

  return {
    subscribe,
    emit,
    isConnected: () => webSocketService.isConnected()
  };
};
