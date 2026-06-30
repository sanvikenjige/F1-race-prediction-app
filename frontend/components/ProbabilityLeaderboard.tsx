// frontend/components/ProbabilityLeaderboard.tsx
'use client';

import { DriverPrediction } from '@/types';
import { DriverCard } from './DriverCard';
import { motion, AnimatePresence } from 'framer-motion';
import { useMemo } from 'react';

interface ProbabilityLeaderboardProps {
  predictions: DriverPrediction[];
  isLoading?: boolean;
}

export const ProbabilityLeaderboard = ({ 
  predictions, 
  isLoading = false 
}: ProbabilityLeaderboardProps) => {
  // Sort predictions by win probability and ensure they don't jump around too much
  const sortedPredictions = useMemo(() => {
    return [...predictions].sort((a, b) => b.win_probability - a.win_probability);
  }, [predictions]);

  if (isLoading && predictions.length === 0) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.1 }}
            className="h-32 bg-gray-800/30 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (predictions.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12 border border-gray-700/50 rounded-lg bg-black/30"
      >
        <div className="text-4xl mb-3">🏁</div>
        <p className="text-gray-400">Waiting for race data...</p>
        <p className="text-sm text-gray-500 mt-2">Connect to a race session to see predictions</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-3"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="text-2xl"
        >
          🏎️
        </motion.div>
        <div>
          <h2 className="text-2xl font-bold text-white">Win Probability Ranking</h2>
          <p className="text-sm text-gray-400">Real-time predictions</p>
        </div>
      </div>

      {/* Predictions List */}
      <AnimatePresence mode="popLayout">
        <motion.div className="space-y-3">
          {sortedPredictions.map((driver, index) => (
            <motion.div
              key={driver.driver_number}
              layout
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{
                duration: 0.3,
                type: 'spring',
                stiffness: 300,
                damping: 30
              }}
            >
              {/* Rank Badge */}
              <div className="flex items-start gap-3">
                <motion.div
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  className={`
                    w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg
                    transition-all
                    ${index === 0 
                      ? 'bg-gradient-to-br from-yellow-500 to-orange-500 text-black' 
                      : index === 1 
                      ? 'bg-gradient-to-br from-gray-400 to-gray-500 text-black' 
                      : index === 2 
                      ? 'bg-gradient-to-br from-amber-600 to-amber-700 text-white'
                      : 'bg-gray-800/50 text-white border border-gray-700/50'
                    }
                  `}
                >
                  {index + 1}
                </motion.div>
                
                <div className="flex-1">
                  <DriverCard 
                    driver={driver} 
                    index={index}
                    isHighlighted={index < 3}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>

      {/* Stats Footer */}
      {sortedPredictions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-6 pt-4 border-t border-gray-700/50"
        >
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-gray-400 mb-1">Leaders Avg Prob</div>
              <div className="text-lg font-bold text-[#E10600]">
                {(sortedPredictions.slice(0, 3).reduce((sum, p) => sum + (p.win_probability ?? 0), 0) / 3 * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-1">Highest Prob</div>
              <div className="text-lg font-bold text-white">
                {((sortedPredictions[0]?.win_probability ?? 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-1">Total Drivers</div>
              <div className="text-lg font-bold text-white">
                {sortedPredictions.length}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};