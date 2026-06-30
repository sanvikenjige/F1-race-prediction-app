import type { Metadata, Viewport } from 'next';
import { AnimatedBackground } from '@/components/AnimatedBackground';
import './globals.css';
 
export const metadata: Metadata = {
  title: 'F1 Race Winner Prediction - Live AI Analysis',
  description: 'Real-time Formula 1 race winner predictions powered by machine learning and live telemetry data',
  keywords: ['Formula 1', 'F1', 'Prediction', 'AI', 'Machine Learning', 'Racing', 'Live Data'],
  icons: {
    icon: '🏁'
  }
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1
};
 
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0A0A0A] text-white overflow-x-hidden">
        <AnimatedBackground />
        
        {/* Main Content */}
        <div className="relative z-10 min-h-screen">
          <div className="max-w-7xl mx-auto px-4 py-8">
            {children}
          </div>
        </div>
 
        {/* Footer */}
        <footer className="relative z-10 border-t border-gray-700/50 mt-12 py-6 px-4">
          <div className="max-w-7xl mx-auto text-center text-gray-400 text-sm">
            <p>🏁 F1 Race Winner Prediction Engine v1.0 | Powered by OpenF1 API & LightGBM ML</p>
            <p className="mt-2 text-xs text-gray-500">
              Real-time telemetry analysis • Sub-100ms inference • Premium racing aesthetic
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
