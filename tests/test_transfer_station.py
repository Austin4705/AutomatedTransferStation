"""Tests for the Transfer_Station ABC and VirtualTransferStation."""

import pytest
from ats.transfer_station import Transfer_Station, VirtualTransferStation


class TestVirtualTransferStation:
    """Verify the virtual driver tracks positions and prints commands."""

    def setup_method(self):
        # Ensure Logger doesn't try to send via websocket during tests
        from ats.logger import Logger
        from unittest.mock import MagicMock
        Logger.socket_manager = MagicMock()
        self.ts = VirtualTransferStation()

    def test_initial_position(self):
        assert self.ts.posX() == 0.0
        assert self.ts.posY() == 0.0
        assert self.ts.posZ() == 0.0

    def test_absolute_move(self):
        self.ts.moveX(10.5)
        self.ts.moveY(-3.2)
        self.ts.moveZ(1.0)
        assert self.ts.posX() == 10.5
        assert self.ts.posY() == -3.2
        assert self.ts.posZ() == 1.0

    def test_relative_move(self):
        self.ts.moveX(5.0)
        self.ts.moveXRel(2.0)
        assert self.ts.posX() == 7.0

        self.ts.moveY(10.0)
        self.ts.moveYRel(-3.0)
        assert self.ts.posY() == 7.0

    def test_move_xy(self):
        self.ts.moveXY(1.0, 2.0)
        assert self.ts.posX() == 1.0
        assert self.ts.posY() == 2.0

    def test_move_xy_rel(self):
        self.ts.moveXY(5.0, 5.0)
        self.ts.moveXYRel(-1.0, 2.0)
        assert self.ts.posX() == 4.0
        assert self.ts.posY() == 7.0

    def test_led_does_not_crash(self):
        self.ts.led_on()
        self.ts.led_off()
        self.ts.setLED(True)
        self.ts.setLED(False)

    def test_command_history(self):
        self.ts.add_fake_command("test_cmd")
        history = self.ts.get_send_command_history()
        assert len(history) == 1
        assert history[0]['command'] == "test_cmd"


class TestDriverRegistry:
    """Verify the @register decorator and factory pattern."""

    def test_virtual_registered(self):
        assert "virtual" in Transfer_Station._registry

    def test_create_virtual(self):
        from ats.logger import Logger
        from unittest.mock import MagicMock
        Logger.socket_manager = MagicMock()
        ts = Transfer_Station.create("virtual")
        assert isinstance(ts, VirtualTransferStation)

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown station type"):
            Transfer_Station.create("nonexistent_driver_xyz")

    def test_custom_driver_registration(self):
        """Verify a user can register their own driver at runtime."""
        from ats.logger import Logger
        from unittest.mock import MagicMock
        Logger.socket_manager = MagicMock()

        @Transfer_Station.register("test_custom")
        class CustomStation(VirtualTransferStation):
            pass

        ts = Transfer_Station.create("test_custom")
        assert isinstance(ts, CustomStation)

        # Clean up
        del Transfer_Station._registry["test_custom"]

