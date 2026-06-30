// frontend/components/LiveDashboard.tsx
'use client';

import { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ProbabilityLeaderboard } from './ProbabilityLeaderboard';
import { TrackStatus } from './TrackStatus';
import { LiveMetrics } from './LiveMetrics';
import { RaceResultPanel } from './RaceResultPanel';
import {
  LiveDashboardState,
  RaceResultDriver,
  RaceResultResponse,
  WebSocketMessage
} from '@/types';

interface LiveDashboardProps {
  sessionKey?: number;
  raceName?: string;
  raceLocation?: string;
  raceStatus?: string;
  raceDate?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const formatRaceDate = (value?: string) => {
  if (!value) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  }).format(date);
};

const getRaceStatusLabel = (status?: string) => {
  if (status === 'completed') return 'Final result';
  if (status === 'live') return 'Live race';
  if (status === 'upcoming') return 'Upcoming race';
  return 'Race telemetry';
};

export const LiveDashboard = ({
  sessionKey = 9999,
  raceName = 'Selected Grand Prix',
  raceLocation = 'Live race telemetry',
  raceStatus = 'live',
  raceDate
}: LiveDashboardProps) => {
  const isCompletedRace = raceStatus === 'completed';
  const [state, setState] = useState<LiveDashboardState>({
    isConnected: false,
    isLoading: !isCompletedRace,
    predictions: [],
    trackStatus: null,
    inferenceStats: null,
    error: null,
    lastUpdate: null
  });
  const [resultState, setResultState] = useState<{
    isLoading: boolean;
    winner: RaceResultDriver | null;
    classification: RaceResultDriver[];
    error: string | null;
  }>({
    isLoading: isCompletedRace,
    winner: null,
    classification: [],
    error: null
  });

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'predictions') {
      setState(prev => ({
        ...prev,
        predictions: message.predictions || [],
        trackStatus: message.track_status || null,
        inferenceStats: message.inference_stats || null,
        isLoading: false,
        lastUpdate: new Date(),
        error: null
      }));
    } else if (message.type === 'connection') {
      console.log('Connected:', message.message);
    } else if (message.type === 'error') {
      setState(prev => ({
        ...prev,
        error: message.message || 'Unknown error occurred',
        isLoading: false
      }));
    }
  }, []);

  const handleError = useCallback((error: Error) => {
    console.error('WebSocket error:', error);
    setState(prev => ({
      ...prev,
      error: error.message,
      isLoading: false
    }));
  }, []);

  const handleStatusChange = useCallback((status: 'connecting' | 'connected' | 'disconnected') => {
    setState(prev => ({
      ...prev,
      isConnected: status === 'connected',
      isLoading: !isCompletedRace && status === 'connecting'
    }));
  }, [isCompletedRace]);

  const { subscribe, isConnected } = useWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/live-predictions',
    onMessage: handleMessage,
    onError: handleError,
    onStatusChange: handleStatusChange,
    autoConnect: !isCompletedRace
  });

  useEffect(() => {
    if (!isCompletedRace && isConnected && sessionKey) {
      subscribe(sessionKey, 5);
    }
  }, [isCompletedRace, isConnected, sessionKey, subscribe]);

  useEffect(() => {
    if (!isCompletedRace || !sessionKey) {
      return;
    }

    const fetchRaceResult = async () => {
      try {
        setResultState(prev => ({ ...prev, isLoading: true, error: null }));

        const response = await fetch(`${API_BASE_URL}/api/race-result/${sessionKey}`);
        if (!response.ok) {
          throw new Error(`Final result unavailable (${response.status})`);
        }

        const result = (await response.json()) as RaceResultResponse;
        setResultState({
          isLoading: false,
          winner: result.winner,
          classification: result.classification || [],
          error: null
        });
      } catch (error) {
        setResultState({
          isLoading: false,
          winner: null,
          classification: [],
          error: error instanceof Error ? error.message : 'Final result unavailable'
        });
      }
    };

    fetchRaceResult();
  }, [isCompletedRace, sessionKey]);

  const raceDateLabel = formatRaceDate(raceDate);
  const visibleError = state.error || resultState.error;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full space-y-6"
    >
      <motion.div
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        className="mb-8 text-center"
      >
        <div className="mb-3 text-sm font-semibold uppercase tracking-wide text-[#E10600]">
          {getRaceStatusLabel(raceStatus)}
        </div>
        <h1 className="mb-2 text-4xl font-bold md:text-5xl">
          <span className="text-white">{raceName}</span>{' '}
          <span className="bg-gradient-to-r from-[#E10600] to-red-400 bg-clip-text text-transparent">
            {isCompletedRace ? 'Result' : 'Prediction'}
          </span>
        </h1>
        <p className="text-lg text-gray-400">
          {raceLocation}
          {raceDateLabel ? ` - ${raceDateLabel}` : ''}
        </p>
      </motion.div>

      {visibleError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-red-500/50 bg-red-500/10 p-4"
        >
          <div className="font-semibold text-white">Data issue</div>
          <div className="text-sm text-red-200">{visibleError}</div>
        </motion.div>
      )}

      {!isCompletedRace && (
        <>
          <LiveMetrics stats={state.inferenceStats} isConnected={state.isConnected} />

          {state.trackStatus && (
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }}>
              <TrackStatus status={state.trackStatus} />
            </motion.div>
          )}
        </>
      )}

      <motion.div
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        transition={{ delay: 0.2 }}
        className="rounded-lg border border-gray-700/50 bg-black/40 p-6 backdrop-blur-sm"
      >
        {isCompletedRace ? (
          <RaceResultPanel
            winner={resultState.winner}
            isLoading={resultState.isLoading}
          />
        ) : (
          <ProbabilityLeaderboard
            predictions={state.predictions}
            isLoading={state.isLoading && state.predictions.length === 0}
          />
        )}
      </motion.div>

      {state.lastUpdate && !isCompletedRace && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center text-sm text-gray-400"
        >
          Last updated: {state.lastUpdate.toLocaleTimeString()}
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="rounded-lg border border-gray-700/50 bg-black/30 p-4"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-400">
              {isCompletedRace ? 'Showing final result for' : 'Analyzing'}
            </div>
            <div className="text-lg font-bold text-white">{raceName}</div>
            <div className="text-xs text-gray-500">{raceLocation}</div>
          </div>
          <div
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 ${
              isCompletedRace || state.isConnected
                ? 'border-green-500/50 bg-green-500/20'
                : 'border-red-500/50 bg-red-500/20'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isCompletedRace || state.isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm font-semibold text-white">
              {isCompletedRace ? 'FINAL' : state.isConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};
