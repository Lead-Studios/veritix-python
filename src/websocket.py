# app/main.py
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import JSONResponse
from src.manager import TicketScanManager
from src.schemas import TicketScan
from datetime import datetime
from src.logging_config import setup_logging, log_info, log_error, WEBSOCKET_CONNECTIONS

# Set up structured logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
setup_logging(LOG_LEVEL)
logger = logging.getLogger("ticket_scans.app")

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
    WEBSOCKET_CONNECTIONS.inc()
    log_info("WebSocket connection established")
    try:
        # Keep the connection alive; optionally handle incoming messages if needed.
        while True:
            # Wait for any message from client; if you don't expect messages you can await ws.receive_text()
            # but we will use receive to detect disconnects from client side.
            try:
                data = await ws.receive_text()
                # For now, we simply ignore messages from clients but log them
                log_info("Received message from client (ignored)", {"message_length": len(data)})
            except Exception:
                # The client may close the connection — break to disconnect and cleanup
                break
    except WebSocketDisconnect:
        log_info("Client disconnected via WebSocketDisconnect")
    except Exception as e:
        log_error("Unexpected error in websocket loop", {"error": str(e)})
    finally:
        await manager.disconnect(ws)
        WEBSOCKET_CONNECTIONS.dec()
        log_info("WebSocket connection closed")

@router.post("/scans", response_class=JSONResponse)
async def post_scan(scan: TicketScan):
    """
    POST endpoint to accept a scan and broadcast it to clients.
    In production, scanning devices/services would typically call this API when a ticket is scanned,
    or you would call manager.broadcast_scan from inside your event pipeline.
    """
    log_info("Ticket scan received", {
        "ticket_id": scan.ticket_id,
        "event_id": scan.event_id,
        "scanner_id": scan.scanner_id
    })
    payload = scan.dict()
    # Optionally add server-received timestamp
    payload.setdefault("server_received_at", datetime.utcnow().isoformat())
    # Broadcast but don't block the response when there are many clients (we await because manager.broadcast_scan is async)
    await manager.broadcast_scan(payload)
    log_info("Ticket scan processed successfully", {
        "ticket_id": scan.ticket_id,
        "event_id": scan.event_id
    })
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    await manager.start_cleanup_task()
    log_info("WebSocket service started", {
        "session_timeout_minutes": SESSION_TIMEOUT_MINUTES
    })


@app.on_event("shutdown")
async def shutdown_event():
    await manager.stop_cleanup_task()
    log_info("WebSocket service shutdown completed")


app.include_router(router)
