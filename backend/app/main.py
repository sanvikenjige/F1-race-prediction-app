# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json

from app.config import settings
from app.websocket_manager import manager
from app.ml.live_inference import get_live_inference
from app.data.openf1_client import get_openf1_client
from app.data.data_processor import RaceDataProcessor
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# ==================== REQUEST MODELS ====================

class SessionRequest(BaseModel):
    """Request body for session operations."""
    session_key: int

# Global state
race_session = None
inference_task = None
RACE_CACHE_DIR = Path(__file__).resolve().parent / "data" / "cache"
_race_sessions_cache: Dict[int, List[Dict]] = {}
_race_results_cache: Dict[int, Dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    logger.info("🏁 F1 Race Prediction Service Starting...")
    
    # Startup
    try:
        inference = await get_live_inference()
        logger.info("✅ Live inference engine initialized")
    except Exception as e:
        logger.error(f"❌ Error initializing inference engine: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("🛑 F1 Race Prediction Service Shutting Down...")

# Create FastAPI app
app = FastAPI(
    title="F1 Race Winner Prediction API",
    description="Real-time Formula 1 race winner prediction with live data updates",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HEALTH CHECKS ====================

@app.get("/health")
async def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "F1 Race Prediction API",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/stats")
async def get_stats() -> Dict:
    """Get system statistics."""
    inference = await get_live_inference()
    ws_stats = manager.get_stats()
    inference_stats = inference.get_inference_stats()
    
    return {
        "websocket": ws_stats,
        "inference": inference_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== API ENDPOINTS ====================

def _parse_openf1_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _race_status(session: Dict) -> str:
    now = datetime.now(timezone.utc)
    start = _parse_openf1_datetime(session.get("date_start"))
    end = _parse_openf1_datetime(session.get("date_end"))

    if start and end and start <= now <= end:
        return "live"
    if start and now < start:
        return "upcoming"
    return "completed"


def _cache_path_for_year(year: int) -> Path:
    return RACE_CACHE_DIR / f"races_{year}.json"


def _result_cache_path(session_key: int) -> Path:
    return RACE_CACHE_DIR / f"race_result_{session_key}.json"


def _read_cached_sessions(year: int) -> List[Dict]:
    if year in _race_sessions_cache:
        return _race_sessions_cache[year]

    cache_path = _cache_path_for_year(year)
    if not cache_path.exists():
        return []

    try:
        sessions = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(sessions, list):
            _race_sessions_cache[year] = sessions
            return sessions
    except Exception as e:
        logger.warning(f"Could not read race cache for {year}: {str(e)}")

    return []


def _write_cached_sessions(year: int, sessions: List[Dict]) -> None:
    if not sessions:
        return

    try:
        RACE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path_for_year(year).write_text(
            json.dumps(sessions, ensure_ascii=False),
            encoding="utf-8"
        )
        _race_sessions_cache[year] = sessions
    except Exception as e:
        logger.warning(f"Could not write race cache for {year}: {str(e)}")


def _read_cached_race_result(session_key: int) -> Optional[Dict]:
    if session_key in _race_results_cache:
        return _race_results_cache[session_key]

    cache_path = _result_cache_path(session_key)
    if not cache_path.exists():
        return None

    try:
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(result, dict):
            _race_results_cache[session_key] = result
            return result
    except Exception as e:
        logger.warning(f"Could not read race result cache for {session_key}: {str(e)}")

    return None


def _write_cached_race_result(session_key: int, result: Dict) -> None:
    if not result:
        return

    try:
        RACE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _result_cache_path(session_key).write_text(
            json.dumps(result, ensure_ascii=False),
            encoding="utf-8"
        )
        _race_results_cache[session_key] = result
    except Exception as e:
        logger.warning(f"Could not write race result cache for {session_key}: {str(e)}")


async def _get_sessions_with_fallback(client, requested_year: int) -> tuple[int, List[Dict], str]:
    candidate_years = [
        requested_year,
        requested_year - 1,
        requested_year - 2,
        requested_year + 1,
    ]

    seen_years = set()
    for candidate_year in candidate_years:
        if candidate_year in seen_years:
            continue
        seen_years.add(candidate_year)

        sessions = await client.get_sessions(year=candidate_year)
        if sessions:
            _write_cached_sessions(candidate_year, sessions)
            return candidate_year, sessions, "live"

        cached_sessions = _read_cached_sessions(candidate_year)
        if cached_sessions:
            return candidate_year, cached_sessions, "cache"

    return requested_year, [], "empty"


def _normalize_race_sessions(sessions: List[Dict]) -> List[Dict]:
    race_sessions = [
        {
            **session,
            "race_status": _race_status(session)
        }
        for session in sessions
        if str(session.get("session_name", "")).lower() == "race"
    ]

    if not race_sessions:
        race_sessions = [
            {
                **session,
                "race_status": _race_status(session)
            }
            for session in sessions
        ]

    status_order = {"live": 0, "upcoming": 1, "completed": 2}
    race_sessions.sort(
        key=lambda session: (
            status_order.get(session.get("race_status"), 3),
            session.get("date_start") or ""
        )
    )

    return race_sessions


def _driver_display_name(driver: Dict) -> str:
    return (
        driver.get("broadcast_name")
        or driver.get("full_name")
        or driver.get("name_acronym")
        or "Unknown"
    )


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _build_final_classification(
    result_data: List[Dict],
    drivers: List[Dict],
    grid_data: List[Dict],
    positions_data: List[Dict]
) -> List[Dict]:
    drivers_by_number = {
        driver.get("driver_number"): driver
        for driver in drivers
        if driver.get("driver_number") is not None
    }
    grid_by_number = {
        row.get("driver_number"): row
        for row in grid_data
        if row.get("driver_number") is not None
    }

    if result_data:
        rows = result_data
    else:
        latest_positions = {}
        for row in positions_data:
            driver_number = row.get("driver_number")
            if driver_number is not None:
                latest_positions[driver_number] = row
        rows = list(latest_positions.values())

    classification = []
    for row in rows:
        driver_number = row.get("driver_number")
        driver = drivers_by_number.get(driver_number, {})
        grid = grid_by_number.get(driver_number, {})
        position = _safe_int(row.get("position"), 99)

        classification.append({
            "driver_number": driver_number,
            "driver_name": _driver_display_name(driver),
            "team_name": driver.get("team_name", "Unknown"),
            "position": position,
            "grid_position": _safe_int(grid.get("position") or row.get("grid_position"), 0),
            "result_status": row.get("result_status") or row.get("status") or "CLASSIFIED",
            "laps_completed": row.get("number_of_laps") or row.get("laps_completed"),
            "duration": row.get("duration"),
            "points": row.get("points")
        })

    return sorted(classification, key=lambda row: row.get("position") or 99)


@app.get("/api/races")
async def get_races(year: Optional[int] = None, include_completed: bool = False) -> Dict:
    """
    Fetch user-facing Formula 1 race sessions for the selected season.
    """
    try:
        selected_year = year or datetime.utcnow().year
        client = await get_openf1_client()
        response_year, sessions, source = await _get_sessions_with_fallback(client, selected_year)
        race_sessions = _normalize_race_sessions(sessions)

        if not include_completed:
            race_sessions = [
                race
                for race in race_sessions
                if race.get("race_status") != "completed"
            ]
        
        return {
            "status": "success",
            "year": response_year,
            "requested_year": selected_year,
            "source": source,
            "data": race_sessions,
            "count": len(race_sessions),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching races: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_key}")
async def get_session_data(session_key: int) -> Dict:
    """
    Fetch comprehensive data for a specific session.
    """
    try:
        client = await get_openf1_client()
        processor = RaceDataProcessor()
        
        # Fetch all telemetry data
        telemetry = await client.fetch_race_telemetry(session_key)
        
        if not telemetry:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "status": "success",
            "data": telemetry,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/race-result/{session_key}")
async def get_race_result(session_key: int) -> Dict:
    """
    Fetch final classification for a completed race.
    """
    try:
        client = await get_openf1_client()

        result_data = await client.get_session_result(session_key)
        drivers = await client.get_drivers(session_key)
        grid_data = await client.get_starting_grid(session_key)
        positions_data = await client.get_positions(session_key) if not result_data else []
        classification = _build_final_classification(
            result_data,
            drivers,
            grid_data,
            positions_data
        )

        if not classification:
            cached_result = _read_cached_race_result(session_key)
            if cached_result:
                return {
                    **cached_result,
                    "source": f"{cached_result.get('source', 'cache')}_cache",
                }
            raise HTTPException(status_code=404, detail="Race result not available")

        payload = {
            "status": "success",
            "session_key": session_key,
            "winner": classification[0],
            "classification": classification,
            "source": "session_result" if result_data else "position",
            "timestamp": datetime.utcnow().isoformat()
        }
        _write_cached_race_result(session_key, payload)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching race result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict")
async def predict_winners(session_key: int, top_n: int = 5) -> Dict:
    """
    Get win probability predictions for all drivers in a session.
    """
    try:
        client = await get_openf1_client()
        inference = await get_live_inference()
        processor = RaceDataProcessor()
        
        # Fetch live telemetry
        telemetry = await client.fetch_race_telemetry(session_key)
        drivers = await client.get_drivers(session_key)
        
        if not telemetry or not drivers:
            raise HTTPException(status_code=404, detail="Session data not found")
        
        # Get grid positions (from a static mapping or session data)
        grid_positions = {d.get('driver_number'): i+1 for i, d in enumerate(drivers)}
        
        # Process data
        positions = processor.process_positions_data(telemetry.get('positions', []))
        intervals = processor.process_intervals_data(telemetry.get('intervals', []))
        laps = processor.process_laps_data(telemetry.get('laps', []))
        stints = processor.process_stints_data(telemetry.get('stints', []))
        track_status = processor.process_track_status(telemetry.get('track_status', []))
        
        # Aggregate driver data
        drivers_data, _ = processor.validate_data_quality(
            processor.aggregate_driver_data(positions, intervals, laps, stints, grid_positions, drivers)
        )
        
        if not drivers_data:
            raise HTTPException(status_code=400, detail="No valid driver data")
        
        # Get predictions
        predictions = await inference.predict_top_finishers(drivers_data, top_n=top_n)
        
        return {
            "status": "success",
            "predictions": predictions,
            "track_status": track_status,
            "inference_stats": inference.get_inference_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SESSION VALIDATION ====================

@app.post("/api/validate-session")
async def validate_session(request: SessionRequest) -> Dict:
    """
    Check if a session has real race data before connecting WebSocket.
    
    Request body:
    {
        "session_key": 9472
    }
    
    Returns:
    {
        "has_data": bool,
        "drivers_detected": int,
        "laps_completed": int,
        "status": str,
        "message": str
    }
    """
    try:
        session_key = request.session_key
        client = await get_openf1_client()
        
        # Fetch telemetry for this session
        telemetry = await client.fetch_race_telemetry(session_key)
        
        if not telemetry:
            return {
                "has_data": False,
                "status": "No data",
                "drivers_detected": 0,
                "laps_completed": 0,
                "message": "This session has no telemetry data available"
            }
        
        laps = telemetry.get('laps', [])
        intervals = telemetry.get('intervals', [])
        
        # Check if race has started/has data
        completed_laps = len([l for l in laps if l.get('lap_number')])
        unique_drivers = len(set(l.get('driver_number') for l in laps if l.get('driver_number')))
        
        # Consider it "has data" if we have multiple drivers with lap data
        has_real_data = completed_laps > 0 and unique_drivers > 5
        
        status_msg = ""
        if has_real_data:
            status_msg = f"✅ Live race data detected ({unique_drivers} drivers, {completed_laps} laps)"
        elif unique_drivers > 0:
            status_msg = f"⏳ Race not started yet ({unique_drivers} drivers registered)"
        else:
            status_msg = "❌ No driver data available for this session"
        
        return {
            "has_data": has_real_data,
            "drivers_detected": unique_drivers,
            "laps_completed": completed_laps,
            "status": "LIVE" if has_real_data else "No data yet",
            "message": status_msg
        }
    
    except Exception as e:
        logger.error(f"Error validating session {session_key}: {str(e)}")
        return {
            "has_data": False,
            "status": "Error",
            "drivers_detected": 0,
            "laps_completed": 0,
            "message": f"Session validation failed: {str(e)}"
        }

# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/ws/live-predictions")
async def websocket_live_predictions(websocket: WebSocket):
    """
    WebSocket endpoint for live race prediction updates.
    
    Accepts messages with format:
    {
        "action": "subscribe",
        "session_key": 9999,
        "update_interval": 5
    }
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "message": "Connected to F1 Live Prediction Service",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        while True:
            # Receive configuration from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                session_key = message.get("session_key")
                update_interval = message.get("update_interval", settings.ws_update_rate)
                
                logger.info(f"Client subscribed to session {session_key}")
                
                # Start prediction updates loop
                try:
                    await broadcast_live_predictions(
                        websocket,
                        session_key,
                        update_interval
                    )
                except asyncio.CancelledError:
                    break
            
            elif message.get("action") == "unsubscribe":
                logger.info("Client unsubscribed")
                await manager.send_personal_message({
                    "type": "unsubscribe",
                    "message": "Unsubscribed from predictions",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                break
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info("WebSocket disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await manager.disconnect(websocket)

async def broadcast_live_predictions(
    websocket: WebSocket,
    session_key: int,
    update_interval: int
) -> None:
    """
    Continuously fetch and broadcast live predictions.
    """
    client = await get_openf1_client()
    inference = await get_live_inference()
    processor = RaceDataProcessor()
    
    while True:
        try:
            # Fetch latest telemetry
            telemetry = await client.fetch_race_telemetry(session_key)
            drivers = await client.get_drivers(session_key)
            
            if telemetry and drivers:
                # Grid positions
                grid_positions = {d.get('driver_number'): i+1 for i, d in enumerate(drivers)}
                
                # Process data
                positions = processor.process_positions_data(telemetry.get('positions', []))
                intervals = processor.process_intervals_data(telemetry.get('intervals', []))
                laps = processor.process_laps_data(telemetry.get('laps', []))
                stints = processor.process_stints_data(telemetry.get('stints', []))
                track_status = processor.process_track_status(telemetry.get('track_status', []))
                
                # Aggregate and validate
                drivers_data, _ = processor.validate_data_quality(
                    processor.aggregate_driver_data(positions, intervals, laps, stints, grid_positions, drivers)
                )
                
                if drivers_data:
                    # Get predictions
                    predictions = await inference.predict_top_finishers(drivers_data, top_n=10)
                    
                    # Prepare message
                    message = {
                        "type": "predictions",
                        "session_key": session_key,
                        "predictions": predictions,
                        "track_status": track_status,
                        "inference_stats": inference.get_inference_stats(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Broadcast to all connected clients
                    await manager.broadcast(message)
            
            # Wait for next update
            await asyncio.sleep(update_interval)
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in live predictions broadcast: {str(e)}")
            await asyncio.sleep(5)  # Wait before retrying

# ==================== STARTUP ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        log_level=settings.log_level.lower()
    )
