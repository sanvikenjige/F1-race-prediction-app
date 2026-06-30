// frontend/components/TrackStatus.tsx
'use client';

import { TrackStatus as TrackStatusType } from '@/types';
import { motion } from 'framer-motion';

interface TrackStatusProps {
  status: TrackStatusType | null;
}

export const TrackStatus = ({ status }: TrackStatusProps) => {
  if (!status) return null;

  const getStatusColor = () => {
    switch (status.status) {
      case 'GREEN':
        return 'bg-green-500/20 border-green-500';
      case 'YELLOW':
        return 'bg-yellow-500/20 border-yellow-500';
      case 'RED':
        return 'bg-red-500/20 border-red-500';
      case 'SAFETY_CAR':
        return 'bg-blue-500/20 border-blue-500';
      default:
        return 'bg-gray-500/20 border-gray-500';
    }
  };

  const getStatusLabel = () => {
    switch (status.status) {
      case 'GREEN':
        return 'All Clear';
      case 'YELLOW':
        return 'Yellow Flag';
      case 'RED':
        return 'Red Flag';
      case 'SAFETY_CAR':
        return 'Safety Car';
      default:
        return status.status;
    }
  };

  const getPulseColor = () => {
    switch (status.status) {
      case 'GREEN':
        return '#22c55e';
      case 'YELLOW':
        return '#eab308';
      case 'RED':
        return '#ef4444';
      case 'SAFETY_CAR':
        return '#3b82f6';
      default:
        return '#6b7280';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`border-2 rounded-lg p-4 ${getStatusColor()}`}
    >
      <div className="flex items-center gap-3">
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
          className="w-4 h-4 rounded-full"
          style={{ backgroundColor: getPulseColor() }}
        />
        <div>
          <div className="text-sm font-semibold text-white">{getStatusLabel()}</div>
          {status.message && (
            <div className="text-xs text-gray-300">{status.message}</div>
          )}
        </div>
      </div>
    </motion.div>
  );
};