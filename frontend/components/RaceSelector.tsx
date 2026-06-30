// frontend/components/RaceSelector.tsx
'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

interface RaceSession {
  session_key: number;
  meeting_name?: string;
  country_name?: string;
  location?: string;
  date_start?: string;
  date_end?: string;
  race_status?: 'live' | 'upcoming' | 'completed';
}

interface RacesResponse {
  status: string;
  year?: number;
  requested_year?: number;
  source?: 'live' | 'cache' | 'empty';
  data?: RaceSession[];
}

interface ValidationResponse {
  has_data: boolean;
  drivers_detected: number;
  laps_completed: number;
  status: string;
  message: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const RACE_CACHE_KEY = 'f1-race-selector:last-good-races';

interface CachedRaces {
  season: number;
  races: RaceSession[];
}

const readCachedRaces = (): CachedRaces | null => {
  try {
    const cached = localStorage.getItem(RACE_CACHE_KEY);
    if (!cached) return null;

    const parsed = JSON.parse(cached) as CachedRaces;
    const activeRaces = (parsed.races || []).filter(
      race => race.race_status !== 'completed'
    );

    if (activeRaces.length) {
      return {
        season: parsed.season,
        races: activeRaces
      };
    }
  } catch {
    localStorage.removeItem(RACE_CACHE_KEY);
  }

  return null;
};

const formatDate = (value?: string) => {
  if (!value) return 'Date unavailable';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';

  return new Intl.DateTimeFormat('en', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  }).format(date);
};

const getRaceTitle = (race: RaceSession) => {
  return race.meeting_name || race.location || race.country_name || 'Formula 1 Grand Prix';
};

const getStatusLabel = (status?: RaceSession['race_status']) => {
  if (status === 'live') return 'Live now';
  if (status === 'upcoming') return 'Upcoming';
  return 'Completed';
};

const getStatusClasses = (status?: RaceSession['race_status']) => {
  if (status === 'live') return 'border-green-500/50 bg-green-500/15 text-green-200';
  if (status === 'upcoming') return 'border-blue-500/50 bg-blue-500/15 text-blue-200';
  return 'border-gray-600/70 bg-gray-700/30 text-gray-300';
};

export const RaceSelector = () => {
  const router = useRouter();
  const [races, setRaces] = useState<RaceSession[]>([]);
  const [selectedRaceKey, setSelectedRaceKey] = useState<number | null>(null);
  const [season, setSeason] = useState<number>(new Date().getFullYear());
  const [isFetchingRaces, setIsFetchingRaces] = useState(true);
  const [isValidating, setIsValidating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchRaces = async () => {
      try {
        setIsFetchingRaces(true);
        setMessage(null);

        const response = await fetch(`${API_BASE_URL}/api/races`);
        if (!response.ok) {
          throw new Error(`Could not load races (${response.status})`);
        }

        const result = (await response.json()) as RacesResponse;
        const loadedRaces = (result.data || []).filter(
          race => race.race_status !== 'completed'
        );

        if (loadedRaces.length > 0) {
          const loadedSeason = result.year || new Date().getFullYear();

          setRaces(loadedRaces);
          setSeason(loadedSeason);
          setSelectedRaceKey(loadedRaces[0]?.session_key ?? null);
          localStorage.setItem(
            RACE_CACHE_KEY,
            JSON.stringify({ season: loadedSeason, races: loadedRaces } satisfies CachedRaces)
          );

          if (result.source === 'cache') {
            setMessage('Showing the last saved race list while live schedule data refreshes.');
          } else if (result.requested_year && result.year && result.requested_year !== result.year) {
            setMessage(`Showing ${result.year} races because ${result.requested_year} data is temporarily unavailable.`);
          }

          return;
        }

        const cached = readCachedRaces();
        if (cached) {
          setRaces(cached.races);
          setSeason(cached.season);
          setSelectedRaceKey(cached.races[0]?.session_key ?? null);
          setMessage('Showing your last loaded race list because the backend returned an empty schedule.');
          return;
        }

        setRaces([]);
        setSelectedRaceKey(null);
        setMessage('No live or upcoming races are available right now. Refresh when the next race weekend is closer.');
      } catch (error) {
        const detail = error instanceof Error ? error.message : 'Could not load races';
        const cached = readCachedRaces();

        if (cached) {
          setRaces(cached.races);
          setSeason(cached.season);
          setSelectedRaceKey(cached.races[0]?.session_key ?? null);
          setMessage(`${detail}. Showing your last loaded race list.`);
          return;
        }

        setMessage(`${detail}. Start the backend server and refresh this page.`);
        setRaces([]);
        setSelectedRaceKey(null);
      } finally {
        setIsFetchingRaces(false);
      }
    };

    fetchRaces();
  }, []);

  const selectedRace = useMemo(() => {
    return races.find((race) => race.session_key === selectedRaceKey) || null;
  }, [races, selectedRaceKey]);

  const actionLabel = useMemo(() => {
    if (isValidating) return 'Checking live data...';
    if (selectedRace?.race_status === 'upcoming') return 'Race Upcoming';
    return 'Show Prediction';
  }, [isValidating, selectedRace]);

  const validateAndOpenDashboard = async () => {
    if (!selectedRace) {
      setMessage('Choose a race first.');
      return;
    }

    const params = new URLSearchParams({
      race: String(selectedRace.session_key),
      name: getRaceTitle(selectedRace),
      location: selectedRace.country_name || selectedRace.location || '',
      status: selectedRace.race_status || 'completed',
      date: selectedRace.date_start || ''
    });

    if (selectedRace.race_status === 'upcoming') {
      setMessage(`${getRaceTitle(selectedRace)} is upcoming. Predictions will be available when live race telemetry starts.`);
      return;
    }

    try {
      setIsValidating(true);
      setMessage(null);

      const response = await fetch(`${API_BASE_URL}/api/validate-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_key: selectedRace.session_key })
      });

      if (!response.ok) {
        throw new Error(`Could not check race data (${response.status})`);
      }

      const validation = (await response.json()) as ValidationResponse;

      if (!validation.has_data) {
        setMessage(validation.message || 'Live telemetry is not available for this race yet.');
        return;
      }

      router.push(`/dashboard?${params.toString()}`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Could not open race dashboard';
      setMessage(detail);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      className="space-y-6"
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-[#E10600]">
            {season} Formula 1
          </p>
          <h2 className="mt-1 text-3xl font-bold text-white">Select a Grand Prix</h2>
          <p className="mt-2 max-w-2xl text-sm text-gray-400">
            Choose a race and the app will use live telemetry from the backend to predict the current winner.
          </p>
        </div>

        <button
          type="button"
          onClick={validateAndOpenDashboard}
          disabled={isFetchingRaces || isValidating || !selectedRace}
          className="inline-flex h-12 items-center justify-center rounded-lg bg-[#E10600] px-5 font-bold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-gray-700 disabled:text-gray-400"
        >
          {actionLabel}
        </button>
      </div>

      {message && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4 text-sm text-yellow-100"
        >
          {message}
        </motion.div>
      )}

      {isFetchingRaces ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, index) => (
            <div
              key={index}
              className="h-40 animate-pulse rounded-lg border border-gray-700/50 bg-black/30"
            />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {races.map((race) => {
            const isSelected = selectedRaceKey === race.session_key;

            return (
              <button
                key={race.session_key}
                type="button"
                onClick={() => setSelectedRaceKey(race.session_key)}
                className={`rounded-lg border p-5 text-left transition ${
                  isSelected
                    ? 'border-[#E10600] bg-[#E10600]/10 shadow-lg shadow-[#E10600]/20'
                    : 'border-gray-700/50 bg-black/30 hover:border-gray-500 hover:bg-black/40'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-lg font-bold text-white">{getRaceTitle(race)}</div>
                    <div className="mt-1 text-sm text-gray-400">
                      {race.country_name || race.location || 'Location unavailable'}
                    </div>
                  </div>
                  <span
                    className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold ${getStatusClasses(
                      race.race_status
                    )}`}
                  >
                    {getStatusLabel(race.race_status)}
                  </span>
                </div>

                <div className="mt-5 border-t border-gray-700/50 pt-4">
                  <div className="text-xs uppercase tracking-wide text-gray-500">Race start</div>
                  <div className="mt-1 font-semibold text-gray-200">{formatDate(race.date_start)}</div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {selectedRace && (
        <div className="rounded-lg border border-gray-700/50 bg-black/30 p-4 text-sm text-gray-300">
          Ready to analyze <span className="font-semibold text-white">{getRaceTitle(selectedRace)}</span>
          {' '}from live race telemetry.
        </div>
      )}
    </motion.section>
  );
};
