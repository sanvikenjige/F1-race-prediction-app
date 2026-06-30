// frontend/app/dashboard/page.tsx
'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { LiveDashboard } from '@/components/LiveDashboard';

function DashboardContent() {
  const searchParams = useSearchParams();
  const raceKey = parseInt(searchParams.get('race') || searchParams.get('session') || '9999', 10);
  const raceName = searchParams.get('name') || 'Selected Grand Prix';
  const raceLocation = searchParams.get('location') || 'Live race telemetry';
  const raceStatus = searchParams.get('status') || 'live';
  const raceDate = searchParams.get('date') || '';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen space-y-8"
    >
      <motion.div
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        className="mb-8 flex items-center justify-between"
      >
        <Link
          href="/"
          className="flex items-center gap-2 text-gray-400 transition-colors hover:text-white"
        >
          Back to races
        </Link>

        <div className="flex items-center gap-2 rounded-lg border border-gray-700/50 bg-black/30 px-4 py-2">
          <span className="h-2 w-2 rounded-full bg-[#E10600]" />
          <span className="text-sm font-semibold text-white">{raceName}</span>
        </div>
      </motion.div>

      <LiveDashboard
        sessionKey={raceKey}
        raceName={raceName}
        raceLocation={raceLocation}
        raceStatus={raceStatus}
        raceDate={raceDate}
      />

      <motion.div
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-12 grid gap-6 md:grid-cols-2"
      >
        <div className="rounded-lg border border-gray-700/50 bg-black/30 p-6">
          <h3 className="mb-4 text-lg font-bold text-white">How to use</h3>
          <ul className="space-y-2 text-sm text-gray-300">
            <li>Select a Formula 1 race from the home page</li>
            <li>View real-time win probability rankings</li>
            <li>Monitor driver pace, tyre age, and race position</li>
            <li>Track lap times and performance trends</li>
            <li>Watch the prediction update as live telemetry changes</li>
          </ul>
        </div>

        <div className="rounded-lg border border-gray-700/50 bg-black/30 p-6">
          <h3 className="mb-4 text-lg font-bold text-white">Understanding metrics</h3>
          <ul className="space-y-2 text-sm text-gray-300">
            <li><span className="text-[#E10600]">Win probability:</span> likelihood of race victory</li>
            <li><span className="text-blue-400">Confidence:</span> data quality score for prediction</li>
            <li><span className="text-green-400">Trend:</span> position momentum</li>
            <li><span className="text-yellow-400">Tyre age:</span> laps on the current compound</li>
          </ul>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="border-t border-gray-700/50 py-8 text-center text-xs text-gray-500"
      >
        <p>F1 Race Winner Prediction Engine - real-time AI analysis</p>
        <p className="mt-2">Updates every 5 seconds - inference target under 100ms</p>
      </motion.div>
    </motion.div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen animate-pulse rounded-lg border border-gray-700/50 bg-black/30" />
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
