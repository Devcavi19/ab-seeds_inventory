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


def test_start_stop_lifecycle_on_forced_configured_instance(monkeypatch):
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
