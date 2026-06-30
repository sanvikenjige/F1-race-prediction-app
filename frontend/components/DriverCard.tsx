// frontend/components/DriverCard.tsx
'use client';

import { DriverPrediction, TYRE_COMPOUNDS, TEAM_COLORS } from '@/types';
import { motion } from 'framer-motion';

interface DriverCardProps {
  driver: DriverPrediction;
  index: number;
  isHighlighted?: boolean;
}

export const DriverCard = ({ driver, index, isHighlighted = false }: DriverCardProps) => {
  const getTrendIcon = () => {
    switch (driver.trend) {
      case 'UP':
        return '📈';
      case 'DOWN':
        return '📉';
      default:
        return '➡️';
    }
  };

  const getTyreColor = () => {
    const tyre = driver.tyre_compound;
    switch (tyre) {
      case 1: return 'bg-red-500'; // SOFT
      case 2: return 'bg-yellow-400'; // MEDIUM
      case 3: return 'bg-white'; // HARD
      case 4: return 'bg-green-500'; // INTERMEDIATE
      case 5: return 'bg-blue-500'; // WET
      default: return 'bg-gray-400';
    }
  };

  const teamColor = TEAM_COLORS[driver.team_name] || '#FFFFFF';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02 }}
      className={`
        relative backdrop-blur-sm border rounded-lg p-4 overflow-hidden
        transition-all duration-300 cursor-pointer
        ${isHighlighted 
          ? 'border-[#E10600] bg-[#E10600]/10 shadow-lg shadow-[#E10600]/50' 
          : 'border-gray-700/50 bg-black/30 hover:bg-black/40'
        }
      `}
    >
      {/* Gradient accent */}
      <div 
        className="absolute top-0 left-0 w-1 h-full"
        style={{ backgroundColor: teamColor }}
      />

      {/* Position Badge */}
      <div className="absolute top-2 right-2 flex items-center gap-2">
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="text-sm font-bold text-[#E10600] bg-black/50 px-2 py-1 rounded"
        >
          P{driver.position ?? '—'}
        </motion.div>
      </div>

      {/* Driver Info */}
      <div className="mb-3">
        <div className="flex items-start justify-between mb-1">
          <div>
            <h3 className="font-bold text-white text-lg">{driver.driver_name}</h3>
            <p className="text-xs text-gray-400">{driver.team_name}</p>
          </div>
          <div className="text-2xl">{getTrendIcon()}</div>
        </div>
      </div>

      {/* Probability Bar */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs font-semibold text-gray-300">Win Probability</span>
          <span className="text-sm font-bold text-[#E10600]">
            {((driver.win_probability ?? 0) * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-800/50 rounded-full h-2 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${(driver.win_probability ?? 0) * 100}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="h-full bg-gradient-to-r from-[#E10600] to-red-400"
          />
        </div>
      </div>

      {/* Confidence */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs font-semibold text-gray-300">Confidence</span>
          <span className="text-xs text-gray-400">
            {((driver.confidence ?? 0) * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-800/50 rounded-full h-1.5 overflow-hidden">
          <div
            style={{ width: `${(driver.confidence ?? 0) * 100}%` }}
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-400"
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        {/* Tyre Info */}
        <div className="bg-black/30 rounded p-2">
          <div className="text-xs text-gray-400 mb-1">Tyre</div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getTyreColor()}`} />
            <span className="text-sm font-semibold text-white">
              {TYRE_COMPOUNDS[driver.tyre_compound]}
            </span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Age: {driver.tyre_age} laps
          </div>
        </div>

        {/* Pace Info */}
        <div className="bg-black/30 rounded p-2">
          <div className="text-xs text-gray-400 mb-1">Pace</div>
          <div className="text-sm font-semibold text-white">
            {(driver.last_lap_time ?? 0).toFixed(2)}s
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Δ {((driver.last_lap_time ?? 0) - (driver.best_lap_time ?? 0)).toFixed(2)}s
          </div>
        </div>

        {/* Gap Info */}
        <div className="bg-black/30 rounded p-2">
          <div className="text-xs text-gray-400 mb-1">Gap</div>
          <div className="text-sm font-semibold text-white">
            {(driver.gap_to_leader ?? 0).toFixed(2)}s
          </div>
          <div className="text-xs text-gray-400 mt-1">to leader</div>
        </div>

        {/* Laps Info */}
        <div className="bg-black/30 rounded p-2">
          <div className="text-xs text-gray-400 mb-1">Progress</div>
          <div className="text-sm font-semibold text-white">
            {(driver.total_laps ?? 0)}/{56}
          </div>
          <div className="text-xs text-gray-400 mt-1">laps</div>
        </div>
      </div>

      {/* Grid Position */}
      <div className="text-xs text-gray-400 border-t border-gray-700/50 pt-2">
        Started P{driver.grid_position ?? '—'} → {(driver.grid_position ?? 0) > (driver.position ?? 0) ? '📈' : '📉'} {Math.abs((driver.grid_position ?? 0) - (driver.position ?? 0))} positions
      </div>
    </motion.div>
  );
};