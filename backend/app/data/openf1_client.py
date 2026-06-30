# backend/app/data/openf1_client.py
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenF1Client:
    """Async client for OpenF1 API integration."""
    
    def __init__(self):
        self.base_url = settings.openf1_base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_timeout = aiohttp.ClientTimeout(total=10)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.request_timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make async HTTP request to OpenF1 API."""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.request_timeout)
        
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(3):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()

                    if response.status == 429 and attempt < 2:
                        retry_after = response.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after else 1.5 * (attempt + 1)
                        logger.warning(f"OpenF1 rate limited {endpoint}; retrying in {delay:.1f}s")
                        await asyncio.sleep(delay)
                        continue

                    logger.warning(f"OpenF1 API returned status {response.status}")
                    return {}
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {endpoint}")
                return {}
            except Exception as e:
                logger.error(f"Error fetching {endpoint}: {str(e)}")
                return {}

        return {}
    
    async def get_sessions(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all available race sessions."""
        params = {}
        if year:
            params['year'] = year
        
        data = await self._make_request('sessions', params)
        return data if isinstance(data, list) else []
    
    async def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Fetch the current active session."""
        sessions = await self.get_sessions()
        if sessions:
            return sessions[0]
        return None
    
    async def get_drivers(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch drivers for a specific session."""
        params = {'session_key': session_key}
        data = await self._make_request('drivers', params)
        return data if isinstance(data, list) else []
    
    async def get_laps(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch lap data for drivers in a session."""
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        
        data = await self._make_request('laps', params)
        return data if isinstance(data, list) else []
    
    async def get_intervals(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch interval data (gaps between drivers)."""
        params = {'session_key': session_key}
        data = await self._make_request('intervals', params)
        return data if isinstance(data, list) else []

    async def get_positions(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch running position data for drivers in a session."""
        params = {'session_key': session_key}
        data = await self._make_request('position', params)
        return data if isinstance(data, list) else []

    async def get_session_result(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch final session classification for completed sessions."""
        params = {'session_key': session_key}
        data = await self._make_request('session_result', params)
        return data if isinstance(data, list) else []

    async def get_starting_grid(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch starting grid data when available."""
        params = {'session_key': session_key}
        data = await self._make_request('starting_grid', params)
        return data if isinstance(data, list) else []
    
    async def get_pit_stops(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch pit stop data."""
        params = {'session_key': session_key}
        data = await self._make_request('pit_stops', params)
        return data if isinstance(data, list) else []
    
    async def get_stints(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch stint data (tyre compound and duration)."""
        params = {'session_key': session_key}
        data = await self._make_request('stints', params)
        return data if isinstance(data, list) else []
    
    async def get_track_status(self, session_key: int) -> List[Dict[str, Any]]:
        """Fetch track status updates."""
        params = {'session_key': session_key}
        data = await self._make_request('track_status', params)
        return data if isinstance(data, list) else []
    
    async def fetch_race_telemetry(self, session_key: int) -> Dict[str, Any]:
        """Fetch comprehensive race telemetry data."""
        try:
            laps = await self.get_laps(session_key)
            intervals = await self.get_intervals(session_key)
            positions = await self.get_positions(session_key)
            pit_stops = await self.get_pit_stops(session_key)
            stints = await self.get_stints(session_key)
            track_status = await self.get_track_status(session_key)
            
            return {
                'laps': laps,
                'intervals': intervals,
                'positions': positions,
                'pit_stops': pit_stops,
                'stints': stints,
                'track_status': track_status,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching race telemetry: {str(e)}")
            return {}

# Global client instance
_client: Optional[OpenF1Client] = None

async def get_openf1_client() -> OpenF1Client:
    """Get or create OpenF1 client instance."""
    global _client
    if _client is None:
        _client = OpenF1Client()
    return _client
