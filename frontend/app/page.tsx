// frontend/app/page.tsx
'use client';

import { RaceSelector } from '@/components/RaceSelector';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen space-y-12"
    >
      {/* Quick Info Banner */}
      <motion.div
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        className="bg-gradient-to-r from-[#E10600]/10 to-red-500/10 border border-[#E10600]/50 rounded-lg p-6"
      >
        <div className="flex items-center gap-3">
          <div className="text-2xl">🚀</div>
          <div>
            <h3 className="font-bold text-white">AI-Powered F1 Predictions</h3>
            <p className="text-sm text-gray-300">Select a race below to see real-time win probability predictions</p>
          </div>
        </div>
      </motion.div>

      {/* Race Selector Component */}
      <RaceSelector />

      {/* Features Section */}
      <motion.div
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mt-16"
      >
        <h2 className="text-3xl font-bold text-center mb-12">Why Choose Us</h2>
        
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: '⚡',
              title: 'Real-Time Predictions',
              desc: 'Live updates every 5 seconds with sub-100ms inference'
            },
            {
              icon: '📊',
              title: 'Real Data Analysis',
              desc: 'Powered by live OpenF1 API telemetry, not synthetic data'
            },
            {
              icon: '🤖',
              title: 'ML-Powered',
              desc: 'LightGBM model trained on historical F1 races'
            }
          ].map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="border border-gray-700/50 rounded-lg p-6 bg-black/30"
            >
              <div className="text-4xl mb-3">{feature.icon}</div>
              <h3 className="font-bold text-white mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="grid md:grid-cols-4 gap-4 py-8 border-y border-gray-700/50"
      >
        {[
          { label: 'Inference Speed', value: '<100ms' },
          { label: 'Update Rate', value: '5 seconds' },
          { label: 'Data Source', value: 'OpenF1 API' },
          { label: 'Model Type', value: 'LightGBM' }
        ].map((stat, i) => (
          <div key={i} className="text-center">
            <div className="text-[#E10600] text-2xl font-bold">{stat.value}</div>
            <div className="text-gray-400 text-sm">{stat.label}</div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}