// frontend/types/index.ts

export interface Driver {
  driver_number: number;
  driver_name: string;
  team_name: string;
  position?: number;
  grid_position?: number;
  gap_to_leader?: number;
  interval_to_ahead?: number;
  last_lap_time?: number;
  best_lap_time?: number;
  avg_lap_time?: number;
  lap_consistency?: number;
  total_laps?: number;
  tyre_compound?: number;
  tyre_age?: number;
  stints_completed?: number;
}

export interface DriverPrediction extends Driver {
  win_probability?: number;
  confidence?: number;
  trend?: 'UP' | 'DOWN' | 'STABLE';
  timestamp?: string;
}

export interface RaceResultDriver extends Driver {
  result_status?: string;
  laps_completed?: number;
  duration?: number | string;
  points?: number;
}

export interface RaceResultResponse {
  status: string;
  session_key: number;
  winner: RaceResultDriver;
  classification: RaceResultDriver[];
  source: 'session_result' | 'position';
  timestamp: string;
}

export interface TrackStatus {
  status: string;
  code: number;
  message: string;
  timestamp?: string;
}

export interface InferenceStats {
  last_inference_time_ms: number;
  total_inferences: number;
  status: 'ok' | 'warning';
}

export interface WebSocketMessage {
  type: 'connection' | 'predictions' | 'error' | 'unsubscribe';
  session_key?: number;
  predictions?: DriverPrediction[];
  track_status?: TrackStatus;
  inference_stats?: InferenceStats;
  message?: string;
  timestamp?: string;
}

export interface LiveDashboardState {
  isConnected: boolean;
  isLoading: boolean;
  predictions: DriverPrediction[];
  trackStatus: TrackStatus | null;
  inferenceStats: InferenceStats | null;
  error: string | null;
  lastUpdate: Date | null;
}

export interface SubscribeMessage {
  action: 'subscribe' | 'unsubscribe';
  session_key: number;
  update_interval?: number;
}

export interface DriverCardProps {
  driver: DriverPrediction;
  index: number;
  isHighlighted?: boolean;
}

export interface TyreInfo {
  compound_id: number;
  compound_name: string;
  age: number;
  max_age: number;
}

export const TYRE_COMPOUNDS: Record<number, string> = {
  1: 'SOFT',
  2: 'MEDIUM',
  3: 'HARD',
  4: 'INTERMEDIATE',
  5: 'WET'
};

export const TEAM_COLORS: Record<string, string> = {
  'Red Bull Racing': '#0600EF',
  'Ferrari': '#DC0000',
  'Mercedes': '#00D2BE',
  'McLaren': '#FF8700',
  'Alpine': '#0082FA',
  'Aston Martin': '#00665E',
  'RB': '#1E3050',
  'Haas': '#FFFFFF',
  'Williams': '#005AFF',
  'Sauber': '#9B0000',
  'Alfa Romeo': '#C92800',
  'Kick Sauber': '#9B0000',
  'AlphaTauri': '#2B4562'
};
