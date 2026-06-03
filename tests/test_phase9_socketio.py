import pytest

from app.socket_server import sio
from app.services import realtime as realtime_service


def test_socketio_server_module_imports():
    assert sio is not None


def test_socketio_required_handlers_exist():
    root_handlers = set(next(iter(sio.handlers.values())))
    expected_handlers = {
        "connect",
        "disconnect",
        "join_order_room",
        "leave_order_room",
        "order_accepted",
        "order_preparing",
        "order_picked_up",
        "order_location",
        "order_delivered",
    }
    assert expected_handlers.issubset(root_handlers)


def test_socketio_server_configuration():
    assert getattr(sio, "async_mode", None) == "asgi"
    root_handlers = set(next(iter(sio.handlers.values())))
    assert "connect" in root_handlers
    assert "disconnect" in root_handlers


def test_realtime_service_helpers_are_callable():
    assert callable(realtime_service.emit_accepted)
    assert callable(realtime_service.emit_preparing)
    assert callable(realtime_service.emit_picked_up)
    assert callable(realtime_service.emit_location)
    assert callable(realtime_service.emit_delivered)
