"""Test WebSocket manager with real connection scenarios"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from nedc_bench.api.services.websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Test WebSocket connection management and replay"""

    @pytest.fixture
    def manager(self):
        """Create WebSocketManager instance"""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket with async methods"""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_with_replay(self, manager, mock_websocket):
        """Test connection with last event replay"""
        job_id = "test-job-123"

        # Store a last event
        test_event = {"status": "processing", "progress": 50}
        await manager.broadcast(job_id, test_event)

        # Connect new websocket
        await manager.connect(job_id, mock_websocket)

        # Should accept connection
        mock_websocket.accept.assert_called_once()

        # Should replay last event
        mock_websocket.send_json.assert_called_once_with(test_event)

        # Should be in connections
        assert mock_websocket in manager._connections[job_id]

    @pytest.mark.asyncio
    async def test_connect_without_replay(self, manager, mock_websocket):
        """Test connection when no last event exists"""
        job_id = "new-job-456"

        await manager.connect(job_id, mock_websocket)

        # Should accept but not send anything
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_json.assert_not_called()

        # Should be in connections
        assert mock_websocket in manager._connections[job_id]

    @pytest.mark.asyncio
    async def test_connect_after_initial(self, manager, mock_websocket):
        """Test connect_after_initial method"""
        job_id = "job-789"

        # Store event first
        test_event = {"status": "completed", "result": {}}
        await manager.broadcast(job_id, test_event)

        # Connect after initial (no accept call)
        await manager.connect_after_initial(job_id, mock_websocket)

        # Should NOT call accept (already accepted)
        mock_websocket.accept.assert_not_called()

        # Should replay last event
        mock_websocket.send_json.assert_called_once_with(test_event)

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_connections(self, manager):
        """Test broadcasting to multiple WebSocket connections"""
        job_id = "multi-job"

        # Create multiple mock websockets
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        # Connect them
        await manager.connect_after_initial(job_id, ws1)
        await manager.connect_after_initial(job_id, ws2)
        await manager.connect_after_initial(job_id, ws3)

        # Broadcast message
        message = {"status": "update", "data": "test"}
        await manager.broadcast(job_id, message)

        # All should receive the message
        ws1.send_json.assert_called_with(message)
        ws2.send_json.assert_called_with(message)
        ws3.send_json.assert_called_with(message)

        # Last event should be stored
        assert manager.get_last_event(job_id) == message

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self, manager):
        """Test broadcast cleans up failed connections"""
        job_id = "cleanup-job"

        # Create websockets - one will fail
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json.side_effect = ConnectionError("Connection lost")

        await manager.connect_after_initial(job_id, ws_good)
        await manager.connect_after_initial(job_id, ws_bad)

        # Broadcast should handle the error
        message = {"status": "test"}
        await manager.broadcast(job_id, message)

        # Good connection should receive message
        ws_good.send_json.assert_called_with(message)

        # Bad connection should be removed
        assert ws_good in manager._connections[job_id]
        assert ws_bad not in manager._connections[job_id]

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_websocket):
        """Test disconnect removes WebSocket from tracking"""
        job_id = "disconnect-job"

        # Connect first
        await manager.connect_after_initial(job_id, mock_websocket)
        assert mock_websocket in manager._connections[job_id]

        # Disconnect
        await manager.disconnect(job_id, mock_websocket)

        # Should be removed
        assert job_id not in manager._connections  # Entire key removed when empty

    @pytest.mark.asyncio
    async def test_disconnect_partial_removal(self, manager):
        """Test disconnect only removes specific connection"""
        job_id = "partial-job"

        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect_after_initial(job_id, ws1)
        await manager.connect_after_initial(job_id, ws2)

        # Disconnect only ws1
        await manager.disconnect(job_id, ws1)

        # ws2 should still be connected
        assert ws1 not in manager._connections[job_id]
        assert ws2 in manager._connections[job_id]

    @pytest.mark.asyncio
    async def test_get_last_event(self, manager):
        """Test retrieving last broadcast event"""
        job_id = "event-job"

        # No event initially
        assert manager.get_last_event(job_id) is None

        # Broadcast events
        event1 = {"status": "started"}
        event2 = {"status": "processing"}
        event3 = {"status": "completed"}

        await manager.broadcast(job_id, event1)
        assert manager.get_last_event(job_id) == event1

        await manager.broadcast(job_id, event2)
        assert manager.get_last_event(job_id) == event2

        await manager.broadcast(job_id, event3)
        assert manager.get_last_event(job_id) == event3

    @pytest.mark.asyncio
    async def test_concurrent_connection_safety(self, manager):
        """Test thread-safe concurrent connections"""
        job_id = "concurrent-job"

        # Create many websockets
        websockets = [AsyncMock() for _ in range(10)]

        # Connect them concurrently
        tasks = [
            manager.connect_after_initial(job_id, ws)
            for ws in websockets
        ]
        await asyncio.gather(*tasks)

        # All should be connected
        assert len(manager._connections[job_id]) == 10

    @pytest.mark.asyncio
    async def test_replay_failure_handling(self, manager):
        """Test graceful handling of replay failures"""
        job_id = "replay-fail"

        # Store an event
        await manager.broadcast(job_id, {"test": "data"})

        # Create websocket that fails on replay
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock(side_effect=Exception("Replay failed"))

        # Connect should handle the failure gracefully
        with patch("nedc_bench.api.services.websocket_manager.logger") as mock_logger:
            await manager.connect(job_id, ws)

            # Should log warning but not crash
            mock_logger.warning.assert_called_once()
            assert "replay failed" in mock_logger.warning.call_args[0][0].lower()

        # Should still be connected despite replay failure
        assert ws in manager._connections[job_id]


# Import patch at module level
from unittest.mock import patch