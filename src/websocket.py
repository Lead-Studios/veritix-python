# app/main.py
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import JSONResponse
from app.manager import TicketScanManager, logger as manager_logger
from app.schemas import TicketScan
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger("ticket_scans.app")
# Keep manager logger consistent
manager_logger.setLevel(logging.INFO)

app = FastAPI(title="Ticket Scans WebSocket Service")
router = APIRouter()

# Get session timeout from environment variable, default to 30 minutes
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
manager = TicketScanManager(session_timeout_minutes=SESSION_TIMEOUT_MINUTES)

@router.websocket("/ws/ticket-scans")
async def websocket_ticket_scans(ws: WebSocket):
    """
    WebSocket endpoint that keeps connection open and sends scans when they are broadcast.
    """
    await manager.connect(ws)
    try:
        # Keep the connection alive; optionally handle incoming messages if needed.
        while True:
            # Wait for any message from client; if you don't expect messages you can await ws.receive_text()
            # but we will use receive to detect disconnects from client side.
            try:
                data = await ws.receive_text()
                # For now, we simply ignore messages from clients but log them
                logger.info("Received message from client (ignored): %s", data)
            except Exception:
                # The client may close the connection — break to disconnect and cleanup
                break
    except WebSocketDisconnect:
        logger.info("Client disconnected via WebSocketDisconnect.")
    except Exception as e:
        logger.exception("Unexpected error in websocket loop: %s", e)
    finally:
        await manager.disconnect(ws)

@router.post("/scans", response_class=JSONResponse)
async def post_scan(scan: TicketScan):
    """
    POST endpoint to accept a scan and broadcast it to clients.
    In production, scanning devices/services would typically call this API when a ticket is scanned,
    or you would call manager.broadcast_scan from inside your event pipeline.
    """
    payload = scan.dict()
    # Optionally add server-received timestamp
    payload.setdefault("server_received_at", datetime.utcnow().isoformat())
    # Broadcast but don't block the response when there are many clients (we await because manager.broadcast_scan is async)
    await manager.broadcast_scan(payload)
    logger.info("Received scan for ticket_id=%s event_id=%s", scan.ticket_id, scan.event_id)
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    await manager.start_cleanup_task()
    logger.info("WebSocket service started with %d minute session timeout", SESSION_TIMEOUT_MINUTES)


@app.on_event("shutdown")
async def shutdown_event():
    await manager.stop_cleanup_task()
    logger.info("WebSocket service shutdown completed")


app.include_router(router)
