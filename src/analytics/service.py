"""Analytics service for tracking ticket scans, transfers, and invalid attempts."""
import json
import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, extract, func, text
from sqlalchemy.orm import Session

from src.analytics.models import (
    AnalyticsStats,
    InvalidAttempt,
    TicketScan,
    TicketTransfer,
    get_session,
)
import src.db as _db
from src.logging_config import log_error, log_info

# Simple in-memory cache: (result, expiry_timestamp)
_trending_cache: Optional[Tuple[List[Dict[str, Any]], float]] = None
_TRENDING_CACHE_TTL = 600  # 10 minutes


class AnalyticsService:
    """Service to handle analytics data storage and retrieval."""
    
    def __init__(self):
        self.logger = logging.getLogger("veritix.analytics")
    
    def log_ticket_scan(
        self, 
        ticket_id: str, 
        event_id: str, 
        scanner_id: Optional[str] = None,
        is_valid: bool = True,
        location: Optional[str] = None,
        device_info: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a ticket scan event."""
        session = None
        try:
            session = get_session()
            scan_record = TicketScan(
                ticket_id=ticket_id,
                event_id=event_id,
                scanner_id=scanner_id,
                is_valid=is_valid,
                location=location,
                device_info=device_info,
                additional_metadata=json.dumps(additional_metadata) if additional_metadata else None
            )
            
            session.add(scan_record)
            session.commit()
            
            log_info("Ticket scan logged", {
                "ticket_id": ticket_id,
                "event_id": event_id,
                "is_valid": is_valid,
                "scanner_id": scanner_id
            })
            
            # Update stats
            self._update_analytics_stats(event_id, increment_scan=True, is_valid=is_valid)
            
        except Exception as e:
            log_error("Failed to log ticket scan", {
                "ticket_id": ticket_id,
                "event_id": event_id,
                "error": str(e)
            })
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()
    
    def log_ticket_transfer(
        self,
        ticket_id: str,
        event_id: str,
        from_user_id: str,
        to_user_id: str,
        transfer_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_successful: bool = True,
        additional_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a ticket transfer event."""
        session = None
        try:
            session = get_session()
            transfer_record = TicketTransfer(
                ticket_id=ticket_id,
                event_id=event_id,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                transfer_reason=transfer_reason,
                ip_address=ip_address,
                user_agent=user_agent,
                is_successful=is_successful,
                additional_metadata=json.dumps(additional_metadata) if additional_metadata else None
            )
            
            session.add(transfer_record)
            session.commit()
            
            log_info("Ticket transfer logged", {
                "ticket_id": ticket_id,
                "event_id": event_id,
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "is_successful": is_successful
            })
            
            # Update stats
            self._update_analytics_stats(event_id, increment_transfer=True, is_successful=is_successful)
            
        except Exception as e:
            log_error("Failed to log ticket transfer", {
                "ticket_id": ticket_id,
                "event_id": event_id,
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "error": str(e)
            })
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()
    
    def log_invalid_attempt(
        self,
        attempt_type: str,
        reason: str,
        ticket_id: Optional[str] = None,
        event_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an invalid attempt."""
        session = None
        try:
            session = get_session()
            invalid_record = InvalidAttempt(
                attempt_type=attempt_type,
                ticket_id=ticket_id,
                event_id=event_id,
                reason=reason,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_metadata=json.dumps(additional_metadata) if additional_metadata else None
            )
            
            session.add(invalid_record)
            session.commit()
            
            log_info("Invalid attempt logged", {
                "attempt_type": attempt_type,
                "ticket_id": ticket_id,
                "event_id": event_id,
                "reason": reason
            })
            
            # Update stats
            self._update_analytics_stats(event_id, increment_invalid=True)
            
        except Exception as e:
            log_error("Failed to log invalid attempt", {
                "attempt_type": attempt_type,
                "ticket_id": ticket_id,
                "event_id": event_id,
                "reason": reason,
                "error": str(e)
            })
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()
    
    def get_stats_for_event(self, event_id: str) -> Dict[str, int]:
        """Get analytics stats for a specific event."""
        session = None
        try:
            session = get_session()
            
            # Get the latest stats record for this event
            latest_stats = session.query(AnalyticsStats).filter(
                AnalyticsStats.event_id == event_id
            ).order_by(desc(AnalyticsStats.stat_date)).first()
            
            if latest_stats:
                return {
                    "event_id": latest_stats.event_id,
                    "scan_count": latest_stats.scan_count,
                    "transfer_count": latest_stats.transfer_count,
                    "invalid_attempt_count": latest_stats.invalid_attempt_count,
                    "valid_scan_count": latest_stats.valid_scan_count,
                    "invalid_scan_count": latest_stats.invalid_scan_count,
                    "successful_transfer_count": latest_stats.successful_transfer_count,
                    "failed_transfer_count": latest_stats.failed_transfer_count,
                    "last_updated": latest_stats.stat_date.isoformat()
                }
            else:
                # If no stats exist, calculate from raw data
                scan_count = session.query(TicketScan).filter(TicketScan.event_id == event_id).count()
                valid_scan_count = session.query(TicketScan).filter(
                    TicketScan.event_id == event_id,
                    TicketScan.is_valid == True
                ).count()
                invalid_scan_count = scan_count - valid_scan_count
                
                transfer_count = session.query(TicketTransfer).filter(TicketTransfer.event_id == event_id).count()
                successful_transfer_count = session.query(TicketTransfer).filter(
                    TicketTransfer.event_id == event_id,
                    TicketTransfer.is_successful == True
                ).count()
                failed_transfer_count = transfer_count - successful_transfer_count
                
                invalid_attempt_count = session.query(InvalidAttempt).filter(InvalidAttempt.event_id == event_id).count()
                
                # Create a stats record for future reference
                stats_record = AnalyticsStats(
                    event_id=event_id,
                    scan_count=scan_count,
                    transfer_count=transfer_count,
                    invalid_attempt_count=invalid_attempt_count,
                    valid_scan_count=valid_scan_count,
                    invalid_scan_count=invalid_scan_count,
                    successful_transfer_count=successful_transfer_count,
                    failed_transfer_count=failed_transfer_count
                )
                session.add(stats_record)
                session.commit()
                
                return {
                    "event_id": event_id,
                    "scan_count": scan_count,
                    "transfer_count": transfer_count,
                    "invalid_attempt_count": invalid_attempt_count,
                    "valid_scan_count": valid_scan_count,
                    "invalid_scan_count": invalid_scan_count,
                    "successful_transfer_count": successful_transfer_count,
                    "failed_transfer_count": failed_transfer_count,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            log_error("Failed to get stats for event", {
                "event_id": event_id,
                "error": str(e)
            })
            raise
        finally:
            if session:
                session.close()
    
    def get_stats_for_all_events(self) -> Dict[str, Dict[str, int]]:
        """Get analytics stats for all events."""
        session = None
        try:
            session = get_session()
            
            # Get all unique event IDs
            event_ids = session.query(TicketScan.event_id).distinct().all()
            event_ids.extend(session.query(TicketTransfer.event_id).distinct().all())
            event_ids.extend(session.query(InvalidAttempt.event_id).distinct().all())
            
            # Remove duplicates and get stats for each event
            unique_event_ids = list(set([eid[0] for eid in event_ids if eid[0]]))
            
            all_stats = {}
            for event_id in unique_event_ids:
                all_stats[event_id] = self.get_stats_for_event(event_id)
            
            return all_stats
            
        except Exception as e:
            log_error("Failed to get stats for all events", {"error": str(e)})
            raise
        finally:
            if session:
                session.close()
    
    def get_recent_scans(self, event_id: str, from_ts: Optional[datetime] = None, to_ts: Optional[datetime] = None, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Get recent scan records for an event with date filtering and pagination."""
        session = None
        try:
            session = get_session()
            
            # Build base query
            query = session.query(TicketScan).filter(TicketScan.event_id == event_id)
            
            # Apply time filters
            if from_ts:
                query = query.filter(TicketScan.scan_timestamp >= from_ts)
            if to_ts:
                query = query.filter(TicketScan.scan_timestamp <= to_ts)
            
            # Get total count for pagination
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            scans = query.order_by(desc(TicketScan.scan_timestamp)).offset(offset).limit(limit).all()
            
            return {
                "data": [{
                    "id": scan.id,
                    "ticket_id": scan.ticket_id,
                    "scanner_id": scan.scanner_id,
                    "scan_timestamp": scan.scan_timestamp.isoformat(),
                    "is_valid": scan.is_valid,
                    "location": scan.location
                } for scan in scans],
                "total": total,
                "page": page,
                "limit": limit,
                "from_ts": from_ts.isoformat() if from_ts else None,
                "to_ts": to_ts.isoformat() if to_ts else None
            }
            
        except Exception as e:
            log_error("Failed to get recent scans", {
                "event_id": event_id,
                "error": str(e)
            })
            raise
        finally:
            if session:
                session.close()

    def get_scans_by_ticket_id(self, ticket_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get scan records for a specific ticket identifier."""
        session = None
        try:
            session = get_session()
            scans = session.query(TicketScan).filter(
                TicketScan.ticket_id == ticket_id
            ).order_by(desc(TicketScan.scan_timestamp)).limit(limit).all()
            return [{
                "id": scan.id,
                "ticket_id": scan.ticket_id,
                "event_id": scan.event_id,
                "scan_timestamp": scan.scan_timestamp.isoformat(),
                "is_valid": scan.is_valid,
                "location": scan.location
            } for scan in scans]
        except Exception as e:
            log_error("Failed to get scans by ticket_id", {
                "ticket_id": ticket_id,
                "error": str(e)
            })
            raise
        finally:
            if session:
                session.close()
    
    def get_recent_transfers(self, event_id: str, from_ts: Optional[datetime] = None, to_ts: Optional[datetime] = None, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Get recent transfer records for an event with date filtering and pagination."""
        session = None
        try:
            session = get_session()
            
            # Build base query
            query = session.query(TicketTransfer).filter(TicketTransfer.event_id == event_id)
            
            # Apply time filters
            if from_ts:
                query = query.filter(TicketTransfer.transfer_timestamp >= from_ts)
            if to_ts:
                query = query.filter(TicketTransfer.transfer_timestamp <= to_ts)
            
            # Get total count for pagination
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            transfers = query.order_by(desc(TicketTransfer.transfer_timestamp)).offset(offset).limit(limit).all()
            
            return {
                "data": [{
                    "id": transfer.id,
                    "ticket_id": transfer.ticket_id,
                    "from_user_id": transfer.from_user_id,
                    "to_user_id": transfer.to_user_id,
                    "transfer_timestamp": transfer.transfer_timestamp.isoformat(),
                    "is_successful": transfer.is_successful,
                    "transfer_reason": transfer.transfer_reason
                } for transfer in transfers],
                "total": total,
                "page": page,
                "limit": limit,
                "from_ts": from_ts.isoformat() if from_ts else None,
                "to_ts": to_ts.isoformat() if to_ts else None
            }
            
        except Exception as e:
            log_error("Failed to get recent transfers", {
                "event_id": event_id,
                "error": str(e)
            })
            raise
        finally:
            if session:
                session.close()
    
    def get_invalid_attempts(self, event_id: str, from_ts: Optional[datetime] = None, to_ts: Optional[datetime] = None, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Get recent invalid attempt records for an event with date filtering and pagination."""
        session = None
        try:
            session = get_session()
            
            # Build base query
            query = session.query(InvalidAttempt).filter(InvalidAttempt.event_id == event_id)
            
            # Apply time filters
            if from_ts:
                query = query.filter(InvalidAttempt.attempt_timestamp >= from_ts)
            if to_ts:
                query = query.filter(InvalidAttempt.attempt_timestamp <= to_ts)
            
            # Get total count for pagination
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            invalid_attempts = query.order_by(desc(InvalidAttempt.attempt_timestamp)).offset(offset).limit(limit).all()
            
            return {
                "data": [{
                    "id": attempt.id,
                    "attempt_type": attempt.attempt_type,
                    "ticket_id": attempt.ticket_id,
                    "attempt_timestamp": attempt.attempt_timestamp.isoformat(),
                    "reason": attempt.reason,
                    "ip_address": attempt.ip_address
                } for attempt in invalid_attempts],
                "total": total,
                "page": page,
                "limit": limit,
                "from_ts": from_ts.isoformat() if from_ts else None,
                "to_ts": to_ts.isoformat() if to_ts else None
            }
            
        except Exception as e:
            log_error("Failed to get invalid attempts", {
                "event_id": event_id,
                "error": str(e)
            })
            raise
        finally:
            if session:
                session.close()
    
    def get_trending_events(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """Return top events by scan velocity over the last N hours.

        Results are cached for 10 minutes to avoid repeated heavy queries.
        Joins with event_sales_summary to include event names where available.
        """
        global _trending_cache

        # Return cached result if still valid
        if _trending_cache is not None:
            cached_result, expiry = _trending_cache
            if time.monotonic() < expiry:
                return cached_result[:limit]

        engine = _db.get_engine()
        if engine is None:
            return []

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        try:
            with engine.connect() as conn:
                # Attempt join with event_sales_summary for event names
                try:
                    result = conn.execute(
                        text("""
                            SELECT ts.event_id,
                                   COALESCE(ess.event_name, ts.event_id) AS event_name,
                                   COUNT(*) AS scan_count
                            FROM ticket_scans ts
                            LEFT JOIN event_sales_summary ess
                                   ON ts.event_id = ess.event_id
                            WHERE ts.scan_timestamp >= :cutoff
                            GROUP BY ts.event_id, ess.event_name
                            ORDER BY scan_count DESC
                            LIMIT :limit
                        """),
                        {"cutoff": cutoff, "limit": limit},
                    )
                    rows = [
                        {
                            "event_id": row[0],
                            "event_name": row[1],
                            "scan_count": int(row[2]),
                            "window_hours": hours,
                        }
                        for row in result
                    ]
                except Exception:
                    # Fallback: query ticket_scans only (event_sales_summary may not exist)
                    result = conn.execute(
                        text("""
                            SELECT event_id, COUNT(*) AS scan_count
                            FROM ticket_scans
                            WHERE scan_timestamp >= :cutoff
                            GROUP BY event_id
                            ORDER BY scan_count DESC
                            LIMIT :limit
                        """),
                        {"cutoff": cutoff, "limit": limit},
                    )
                    rows = [
                        {
                            "event_id": row[0],
                            "event_name": row[0],
                            "scan_count": int(row[1]),
                            "window_hours": hours,
                        }
                        for row in result
                    ]
        except Exception as exc:
            log_error("Failed to get trending events", {"error": str(exc)})
            return []

        # Cache the full ordered result (up to a large limit for reuse)
        _trending_cache = (rows, time.monotonic() + _TRENDING_CACHE_TTL)
        return rows[:limit]

    def get_scan_heatmap(
        self,
        event_id: str,
        filter_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Return hourly scan-density data (24 buckets) for an event.

        Optionally scoped to a single calendar day via *filter_date*.
        Hours with no scans are filled with a count of 0 so the response
        always contains exactly 24 entries.
        """
        session = None
        try:
            session = get_session()

            hour_expr = extract("hour", TicketScan.scan_timestamp)
            query = (
                session.query(
                    hour_expr.label("hour"),
                    func.count(TicketScan.id).label("scan_count"),
                )
                .filter(TicketScan.event_id == event_id)
            )

            if filter_date is not None:
                query = query.filter(
                    func.date(TicketScan.scan_timestamp) == filter_date.isoformat()
                )

            rows = query.group_by(hour_expr).all()

            hour_counts: Dict[int, int] = {
                int(row.hour): int(row.scan_count) for row in rows
            }

            data = [
                {"hour": h, "scan_count": hour_counts.get(h, 0)}
                for h in range(24)
            ]

            peak_hour = max(range(24), key=lambda h: hour_counts.get(h, 0))

            return {"event_id": event_id, "data": data, "peak_hour": peak_hour}

        except Exception as e:
            log_error("Failed to get scan heatmap", {
                "event_id": event_id,
                "error": str(e),
            })
            raise
        finally:
            if session:
                session.close()

    def _update_analytics_stats(self, event_id: str,
                               increment_scan: bool = False, is_valid: bool = True,
                               increment_transfer: bool = False, is_successful: bool = True,
                               increment_invalid: bool = False):
        """Internal method to update analytics stats."""
        session = None
        try:
            session = get_session()
            
            # Get or create stats record for today
            today = datetime.utcnow().date()
            stats_record = session.query(AnalyticsStats).filter(
                AnalyticsStats.event_id == event_id
            ).order_by(desc(AnalyticsStats.stat_date)).first()
            
            if not stats_record or stats_record.stat_date.date() != today:
                # Create a new record for today if one doesn't exist or it's from a different day
                stats_record = AnalyticsStats(
                    event_id=event_id,
                    scan_count=0,
                    transfer_count=0,
                    invalid_attempt_count=0,
                    valid_scan_count=0,
                    invalid_scan_count=0,
                    successful_transfer_count=0,
                    failed_transfer_count=0
                )
                session.add(stats_record)
            
            # Update the counters
            if increment_scan:
                stats_record.scan_count += 1
                if is_valid:
                    stats_record.valid_scan_count += 1
                else:
                    stats_record.invalid_scan_count += 1
            elif increment_transfer:
                stats_record.transfer_count += 1
                if is_successful:
                    stats_record.successful_transfer_count += 1
                else:
                    stats_record.failed_transfer_count += 1
            elif increment_invalid:
                stats_record.invalid_attempt_count += 1
            
            session.commit()
            
        except Exception as e:
            log_error("Failed to update analytics stats", {
                "event_id": event_id,
                "error": str(e)
            })
            if session:
                session.rollback()
        finally:
            if session:
                session.close()


# Global instance
analytics_service = AnalyticsService()