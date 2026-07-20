import threading
from datetime import datetime, timezone

try:
    import turso.sync
except ImportError:
    turso = None


class SyncService:
    """Manages background sync of the local SQLite file against a Turso
    embedded-replica remote via pyturso.

    This is entirely separate from the app's primary DB connection
    (app.extensions.get_db()) - it opens its own dedicated connection
    to the same DATABASE_PATH file purely to drive periodic `.sync()` calls.
    Safely inert (never imports/uses turso) unless both configured and the
    native dependency is actually installed.
    """

    def __init__(self, database_path, sync_url=None, auth_token=None, interval_seconds=300):
        self.database_path = database_path
        self.sync_url = sync_url
        self.auth_token = auth_token
        self.interval_seconds = interval_seconds

        self._thread = None
        self._stop_event = threading.Event()
        self._last_sync_at = None
        self._last_sync_status = None
        self._last_error = None
        self._lock = threading.Lock()
        self.conn = None
        
        if self.is_configured():
            try:
                self.conn = turso.sync.connect(
                    self.database_path,
                    remote_url=self.sync_url,
                    auth_token=self.auth_token,
                )
            except Exception as e:
                print(f"Failed to initialize global sync connection: {e}")

    def is_available(self) -> bool:
        return turso is not None

    def is_configured(self) -> bool:
        return self.is_available() and bool(self.sync_url) and bool(self.auth_token)

    def sync_now(self) -> dict:
        if not self.is_available():
            with self._lock:
                self._last_sync_status = 'unavailable'
                self._last_error = None
                synced_at = self._last_sync_at
            return {'status': 'unavailable', 'synced_at': synced_at, 'error': None}

        if not self.is_configured() or not self.conn:
            with self._lock:
                self._last_sync_status = 'not_configured'
                self._last_error = None
                synced_at = self._last_sync_at
            return {'status': 'not_configured', 'synced_at': synced_at, 'error': None}

        try:
            # Checkpoint the WAL first so that any local writes that were
            # committed outside the Turso connection (e.g. via a raw
            # sqlite3.connect()) are flushed into the main DB file before
            # the sync engine tries to push them.  Without this, the push
            # can fail with "unable to checkpoint synced portion of WAL".
            try:
                self.conn.checkpoint()
            except Exception as ckpt_exc:
                # Log but don't abort — push/pull may still succeed if the
                # WAL is in a consistent state from Turso's perspective.
                print(f"[sync] WAL checkpoint warning (non-fatal): {ckpt_exc}")

            self.conn.push()
            self.conn.pull()
        except Exception as exc:
            with self._lock:
                self._last_sync_status = 'error'
                self._last_error = str(exc)
                synced_at = self._last_sync_at
            return {'status': 'error', 'synced_at': synced_at, 'error': str(exc)}

        synced_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._last_sync_at = synced_at
            self._last_sync_status = 'ok'
            self._last_error = None
        return {'status': 'ok', 'synced_at': synced_at, 'error': None}

    def get_status(self) -> dict:
        with self._lock:
            return {
                'available': self.is_available(),
                'configured': self.is_configured(),
                'last_sync_at': self._last_sync_at,
                'last_sync_status': self._last_sync_status,
                'last_error': self._last_error,
            }

    def _run_loop(self):
        while not self._stop_event.is_set():
            self.sync_now()
            self._stop_event.wait(self.interval_seconds)

    def start(self):
        if self._thread is not None:
            return

        if not self.is_configured():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._thread = None
        self._stop_event = threading.Event()
