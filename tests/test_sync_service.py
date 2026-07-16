import importlib.util
import time

import pytest

from app.services import sync_service as sync_service_module
from app.services.sync_service import SyncService


def test_is_available_reflects_actual_import_state():
    service = SyncService(':memory:')
    expected = importlib.util.find_spec('libsql_experimental') is not None
    assert service.is_available() is expected


def test_is_configured_false_when_url_and_token_none():
    service = SyncService(':memory:')
    assert service.is_configured() is False


def test_is_configured_false_when_unavailable_even_with_credentials(monkeypatch):
    monkeypatch.setattr(sync_service_module, 'libsql', None)
    service = SyncService(':memory:', sync_url='libsql://example', auth_token='token')
    assert service.is_available() is False
    assert service.is_configured() is False


def test_sync_now_on_unconfigured_instance_returns_not_configured(monkeypatch):
    # Force "available" so we exercise the not_configured branch specifically
    # (is_available() is checked first in sync_now(), and in this sandbox
    # libsql_experimental is genuinely not installed - see
    # test_sync_now_on_unavailable_instance_returns_unavailable below for
    # that real-environment case).
    monkeypatch.setattr(sync_service_module, 'libsql', object())
    service = SyncService(':memory:')
    result = service.sync_now()
    assert result['status'] == 'not_configured'
    assert result['error'] is None


def test_sync_now_on_unavailable_instance_returns_unavailable(monkeypatch):
    monkeypatch.setattr(sync_service_module, 'libsql', None)
    service = SyncService(':memory:', sync_url='libsql://example', auth_token='token')
    result = service.sync_now()
    assert result['status'] == 'unavailable'
    assert result['error'] is None


def test_start_on_unconfigured_instance_does_not_spawn_thread():
    service = SyncService(':memory:')
    service.start()
    assert service._thread is None


class _FakeLibsqlConnection:
    """Stand-in for a libsql connection: records sync()/close() calls
    without ever touching the network, regardless of whether the real
    libsql_experimental package happens to be installed."""

    def __init__(self):
        self.sync_calls = 0
        self.close_calls = 0

    def sync(self):
        self.sync_calls += 1

    def close(self):
        self.close_calls += 1


class _FakeLibsqlModule:
    def __init__(self):
        self.connections = []

    def connect(self, **kwargs):
        conn = _FakeLibsqlConnection()
        self.connections.append(conn)
        return conn


class _FailingSyncConnection:
    """Fake connection whose .sync() raises, to exercise the error path."""

    def __init__(self, error):
        self._error = error
        self.close_calls = 0

    def sync(self):
        raise self._error

    def close(self):
        self.close_calls += 1


def test_sync_now_closes_connection_after_successful_sync(monkeypatch):
    fake_libsql = _FakeLibsqlModule()
    monkeypatch.setattr(sync_service_module, 'libsql', fake_libsql)
    service = SyncService(':memory:', sync_url='libsql://example', auth_token='token')

    result = service.sync_now()

    assert result['status'] == 'ok'
    assert len(fake_libsql.connections) == 1
    conn = fake_libsql.connections[0]
    assert conn.sync_calls == 1
    assert conn.close_calls == 1


def test_sync_now_closes_connection_when_sync_raises(monkeypatch):
    failing_conn = _FailingSyncConnection(RuntimeError('sync boom'))

    class _FailingLibsqlModule:
        def connect(self, **kwargs):
            return failing_conn

    monkeypatch.setattr(sync_service_module, 'libsql', _FailingLibsqlModule())
    service = SyncService(':memory:', sync_url='libsql://example', auth_token='token')

    result = service.sync_now()

    assert result['status'] == 'error'
    assert result['error'] == 'sync boom'
    assert failing_conn.close_calls == 1


def test_sync_now_does_not_error_when_connect_itself_raises(monkeypatch):
    # conn is never assigned in this case - guards that close() isn't
    # attempted on None.
    class _RaisingLibsqlModule:
        def connect(self, **kwargs):
            raise RuntimeError('connect boom')

    monkeypatch.setattr(sync_service_module, 'libsql', _RaisingLibsqlModule())
    service = SyncService(':memory:', sync_url='libsql://example', auth_token='token')

    result = service.sync_now()

    assert result['status'] == 'error'
    assert result['error'] == 'connect boom'


def test_start_stop_lifecycle_on_forced_configured_instance(monkeypatch):
    # Fake out the libsql module itself (not sync_now/is_available) so this
    # test is environment-independent: it must never attempt a real network
    # connection whether or not libsql_experimental is actually installed.
    fake_libsql = _FakeLibsqlModule()
    monkeypatch.setattr(sync_service_module, 'libsql', fake_libsql)

    service = SyncService(':memory:', sync_url='libsql://example', auth_token='token',
                           interval_seconds=0.05)
    monkeypatch.setattr(service, 'is_configured', lambda: True)

    call_count = {'n': 0}
    original_sync_now = service.sync_now

    def spy_sync_now():
        call_count['n'] += 1
        return original_sync_now()

    monkeypatch.setattr(service, 'sync_now', spy_sync_now)

    service.start()
    assert service._thread is not None
    assert service._thread.is_alive()

    # Give the loop a couple of iterations worth of time.
    time.sleep(0.2)

    service.stop()
    assert service._thread is None
    assert call_count['n'] >= 1

    # The real sync_now()/_run_loop code path ran (not mocked away) and
    # reached libsql.connect()/.sync() via the fake module - confirming the
    # loop actually exercised the connect->sync flow without any real
    # network attempt, and that every opened connection was closed.
    assert len(fake_libsql.connections) == call_count['n']
    assert all(conn.sync_calls == 1 for conn in fake_libsql.connections)
    assert all(conn.close_calls == 1 for conn in fake_libsql.connections)


def test_get_status_shape_and_values_before_and_after_sync_now():
    service = SyncService(':memory:')

    status_before = service.get_status()
    assert status_before == {
        'available': service.is_available(),
        'configured': False,
        'last_sync_at': None,
        'last_sync_status': None,
        'last_error': None,
    }

    result = service.sync_now()

    status_after = service.get_status()
    assert status_after['last_sync_status'] == result['status']
    assert status_after['last_sync_at'] == result['synced_at']
    assert status_after['last_error'] == result['error']
    assert status_after['configured'] is False
