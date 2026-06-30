// frontend/components/LiveMetrics.tsx
'use client';

import { InferenceStats } from '@/types';
import { motion } from 'framer-motion';

interface LiveMetricsProps {
  stats: InferenceStats | null;
  isConnected: boolean;
}

export const LiveMetrics = ({ stats, isConnected }: LiveMetricsProps) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Connection Status */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`
          border rounded-lg p-4 backdrop-blur-sm
          ${isConnected 
            ? 'border-green-500/50 bg-green-500/10' 
            : 'border-red-500/50 bg-red-500/10'
          }
        `}
      >
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
            className={`
              w-4 h-4 rounded-full
              ${isConnected ? 'bg-green-500' : 'bg-red-500'}
            `}
          />
          <div>
            <div className="text-sm font-semibold text-gray-300">Connection</div>
            <div className="text-lg font-bold text-white">
              {isConnected ? '🟢 LIVE' : '🔴 OFFLINE'}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Inference Time */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="border border-gray-700/50 rounded-lg p-4 backdrop-blur-sm bg-black/30"
      >
        <div className="flex items-center gap-3">
          <div className="text-2xl">⚡</div>
          <div>
            <div className="text-sm font-semibold text-gray-300">Inference Time</div>
            <div className="text-lg font-bold text-[#E10600]">
              {stats?.last_inference_time_ms?.toFixed(1) || '—'}ms
            </div>
          </div>
        </div>
        <div className="text-xs text-gray-400 mt-2">
          Target: &lt;100ms
        </div>
      </motion.div>

      {/* Prediction Count */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="border border-gray-700/50 rounded-lg p-4 backdrop-blur-sm bg-black/30"
      >
        <div className="flex items-center gap-3">
          <div className="text-2xl">📊</div>
          <div>
            <div className="text-sm font-semibold text-gray-300">Total Updates</div>
            <motion.div
              key={stats?.total_inferences}
              initial={{ scale: 1.2 }}
              animate={{ scale: 1 }}
              className="text-lg font-bold text-white"
            >
              {stats?.total_inferences || 0}
            </motion.div>
          </div>
        </div>
        <div className="text-xs text-gray-400 mt-2">
          Status: {stats?.status === 'ok' ? '✅ Optimal' : '⚠️ Slow'}
        </div>
      </motion.div>
    </div>
  );
};