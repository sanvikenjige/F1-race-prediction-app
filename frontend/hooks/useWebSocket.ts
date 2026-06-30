// frontend/hooks/useWebSocket.ts
'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { WebSocketMessage, SubscribeMessage } from '@/types';

interface UseWebSocketProps {
  url: string;
  onMessage: (message: WebSocketMessage) => void;
  onError?: (error: Error) => void;
  onStatusChange?: (status: 'connecting' | 'connected' | 'disconnected') => void;
  autoConnect?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  subscribe: (sessionKey: number, updateInterval?: number) => void;
  unsubscribe: () => void;
  disconnect: () => void;
}

export const useWebSocket = ({
  url,
  onMessage,
  onError,
  onStatusChange,
  autoConnect = true
}: UseWebSocketProps): UseWebSocketReturn => {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_INTERVAL = 3000;

  const connectRef = useRef<(() => void) | null>(null);
  const subscribeRef = useRef<((sessionKey: number, updateInterval?: number) => void) | null>(null);

  const reconnect = useCallback(() => {
    if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttemptsRef.current += 1;
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log(`[WebSocket] Reconnecting... (attempt ${reconnectAttemptsRef.current})`);
        connectRef.current?.();
      }, RECONNECT_INTERVAL);
    } else {
      console.error('[WebSocket] Max reconnection attempts reached');
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log('[WebSocket] Connected to', url);
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onStatusChange?.('connected');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          onMessage(message);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
          onError?.(new Error('Failed to parse WebSocket message'));
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        
        // More specific error message
        const errorMsg = 
          !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN
            ? 'Backend not responding - check if server is running'
            : 'WebSocket connection error';
        
        onError?.(new Error(errorMsg));
        onStatusChange?.('disconnected');
      };

      wsRef.current.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setIsConnected(false);
        onStatusChange?.('disconnected');

        // Attempt to reconnect
        reconnect();
      };
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      onError?.(error instanceof Error ? error : new Error('Connection failed'));
      onStatusChange?.('disconnected');
    }
  }, [url, onMessage, onError, onStatusChange, reconnect]);

  // Store connect in ref so reconnect can access it
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  const subscribe = useCallback((sessionKey: number, updateInterval: number = 5) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] Not connected, attempting to reconnect...');
      setTimeout(() => subscribeRef.current?.(sessionKey, updateInterval), 1000);
      return;
    }

    const message: SubscribeMessage = {
      action: 'subscribe',
      session_key: sessionKey,
      update_interval: updateInterval
    };

    try {
      wsRef.current.send(JSON.stringify(message));
      console.log('[WebSocket] Subscribed to session:', sessionKey);
    } catch (error) {
      console.error('[WebSocket] Failed to subscribe:', error);
      onError?.(error instanceof Error ? error : new Error('Failed to subscribe'));
    }
  }, [onError]);

  // Store subscribe in ref so it can call itself
  useEffect(() => {
    subscribeRef.current = subscribe;
  }, [subscribe]);

  const unsubscribe = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const message: SubscribeMessage = {
      action: 'unsubscribe',
      session_key: 0
    };

    try {
      wsRef.current.send(JSON.stringify(message));
      console.log('[WebSocket] Unsubscribed');
    } catch (error) {
      console.error('[WebSocket] Failed to unsubscribe:', error);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    onStatusChange?.('disconnected');
  }, [onStatusChange]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    subscribe,
    unsubscribe,
    disconnect
  };
};