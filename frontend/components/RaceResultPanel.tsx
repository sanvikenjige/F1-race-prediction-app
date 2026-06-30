// frontend/components/RaceResultPanel.tsx
'use client';

import { motion } from 'framer-motion';
import { RaceResultDriver } from '@/types';

interface RaceResultPanelProps {
  winner: RaceResultDriver | null;
  isLoading?: boolean;
}

const formatPosition = (position?: number) => {
  if (!position) return '-';
  return `P${position}`;
};

export const RaceResultPanel = ({
  winner,
  isLoading = false
}: RaceResultPanelProps) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-40 animate-pulse rounded-lg border border-gray-700/50 bg-black/30" />
        {[...Array(5)].map((_, index) => (
          <div
            key={index}
            className="h-16 animate-pulse rounded-lg border border-gray-700/50 bg-black/30"
          />
        ))}
      </div>
    );
  }

  if (!winner) {
    return (
      <div className="rounded-lg border border-gray-700/50 bg-black/30 py-12 text-center text-gray-400">
        Final classification is not available for this race yet.
      </div>
    );
  }

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg border border-[#E10600]/60 bg-[#E10600]/10 p-6"
      >
        <div className="text-sm font-semibold uppercase tracking-wide text-[#E10600]">
          Race winner
        </div>
        <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-3xl font-bold text-white">{winner.driver_name}</h2>
            <p className="mt-1 text-gray-300">{winner.team_name}</p>
          </div>
          <div className="text-4xl font-black text-white">{formatPosition(winner.position)}</div>
        </div>
        <div className="mt-5 grid gap-3 border-t border-[#E10600]/30 pt-4 text-sm text-gray-300 md:grid-cols-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-gray-500">Status</div>
            <div className="font-semibold text-white">{winner.result_status || 'CLASSIFIED'}</div>
          </div>
          {winner.grid_position ? (
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">Started</div>
              <div className="font-semibold text-white">{formatPosition(winner.grid_position)}</div>
            </div>
          ) : null}
          {winner.points !== undefined ? (
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">Points</div>
              <div className="font-semibold text-white">{winner.points}</div>
            </div>
          ) : null}
        </div>
      </motion.div>
    </div>
  );
};
