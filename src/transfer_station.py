import time
from abc import ABC, abstractmethod
from datetime import datetime
from logger import Logger


class Transfer_Station(ABC):
    """
    Abstract base class for transfer station hardware.

    Subclasses MUST implement the abstract methods (movement, position, LED).
    The base class provides command history tracking, convenience wrappers,
    and a driver registry so new hardware can be added without modifying this
    file.

    To register a new driver::

        @Transfer_Station.register("my_driver")
        class MyStation(Transfer_Station):
            ...
    """

    # --------------- driver registry ---------------
    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str):
        """Class decorator that registers a Transfer_Station subclass under *name*."""
        def decorator(subclass):
            cls._registry[name] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, station_type: str = "virtual"):
        """Factory: create a Transfer_Station by its registered name."""
        driver_cls = cls._registry.get(station_type)
        if driver_cls is None:
            raise ValueError(
                f"Unknown station type: '{station_type}'. "
                f"Registered types: {list(cls._registry.keys())}"
            )
        return driver_cls()

    # --------------- magnification lookup (override per subclass) ---------------
    MAGNIFICATION_TRAVEL: dict = {
        5:   {"x": 1, "y": 1, "wait_time": 1},
        10:  {"x": 1, "y": 1, "wait_time": 1},
        20:  {"x": 1, "y": 1, "wait_time": 1},
        40:  {"x": 1, "y": 1, "wait_time": 1},
        50:  {"x": 1, "y": 1, "wait_time": 1},
        100: {"x": 1, "y": 1, "wait_time": 1},
    }

    # --------------- lifecycle ---------------
    def __init__(self):
        self.command_queue: list = []
        self._send_command_history: list[dict] = []
        self.receive_command_history: list[dict] = []
        self._last_received_index: int = -1
        self._last_sent_index: int = -1
        self.camera_height: int = 1536
        self.camera_width: int = 2048

    # --------------- abstract interface (MUST override) ---------------
    @abstractmethod
    def _send_command(self, command: str):
        """Send a raw command string to the hardware."""
        ...

    @abstractmethod
    def moveX(self, x: float) -> None: ...
    @abstractmethod
    def moveY(self, y: float) -> None: ...
    @abstractmethod
    def moveZ(self, z: float) -> None: ...
    @abstractmethod
    def moveXRel(self, x: float) -> None: ...
    @abstractmethod
    def moveYRel(self, y: float) -> None: ...
    @abstractmethod
    def moveZRel(self, z: float) -> None: ...
    @abstractmethod
    def moveXYRel(self, x: float, y: float) -> None: ...
    @abstractmethod
    def posX(self) -> float: ...
    @abstractmethod
    def posY(self) -> float: ...
    @abstractmethod
    def posZ(self) -> float: ...
    @abstractmethod
    def led_on(self) -> None: ...
    @abstractmethod
    def led_off(self) -> None: ...

    # --------------- convenience (NOT to override) ---------------
    def moveXY(self, x: float, y: float) -> None:
        self.moveX(x)
        self.moveY(y)

    def setLED(self, status: bool) -> None:
        if status:
            self.led_on()
        else:
            self.led_off()

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)

    # --------------- command history ---------------
    @staticmethod
    def time_stamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def get_send_command_history(self, depth: int = -1):
        if depth == -1:
            return self._send_command_history
        return self._send_command_history[-depth:]

    def receive_command(self, depth: int = -1):
        self._last_received_index = len(self.receive_command_history)
        return self.receive_command_history[-1]

    def receive_commands(self, depth: int = -1):
        self._last_received_index = len(self.receive_command_history)
        if depth == -1:
            return self.receive_command_history
        return self.receive_command_history[-depth:]

    def since_last_receive(self):
        if self._last_received_index == -1:
            commands = self.receive_command_history
        else:
            commands = self.receive_command_history[self._last_received_index:]
        self._last_received_index = len(self.receive_command_history)
        return commands

    def sent_commands(self, depth: int = -1):
        if depth == -1:
            return self._send_command_history
        return self._send_command_history[-depth:]

    def since_last_send(self):
        if self._last_sent_index == -1:
            commands = self._send_command_history
        else:
            commands = self._send_command_history[self._last_sent_index:]
        self._last_sent_index = len(self._send_command_history)
        return commands

    def exist_new_sent_commands(self) -> bool:
        return len(self._send_command_history) > self._last_sent_index + 1

    def exist_new_received_commands(self) -> bool:
        return len(self.receive_command_history) > self._last_received_index + 1

    def add_fake_command(self, command: str):
        self._send_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'command': command,
            'response': "Virtual Response"
        })

    def add_response(self, response):
        self.receive_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'response': response
        })

    def add_fake_response(self, response):
        self.receive_command_history.append({
            'timestamp': Transfer_Station.time_stamp(),
            'response': response
        })


# ──────────────────────────────────────────────────────────────
# Built-in Virtual driver (prints every command, useful for dev)
# ──────────────────────────────────────────────────────────────

@Transfer_Station.register("virtual")
class VirtualTransferStation(Transfer_Station):
    """
    A virtual (no-hardware) transfer station that prints every command.
    Useful for development and testing on machines without hardware attached.
    """

    def __init__(self):
        super().__init__()
        self.x: float = 0.0
        self.y: float = 0.0
        self.z: float = 0.0
        Logger.log("[VirtualTS] Initialized virtual transfer station")

    def _send_command(self, command: str):
        Logger.log(f"[VirtualTS] Send Command: {command}")

    def moveX(self, x: float) -> None:
        Logger.log(f"[VirtualTS] moveX → {x}")
        self.x = x

    def moveY(self, y: float) -> None:
        Logger.log(f"[VirtualTS] moveY → {y}")
        self.y = y

    def moveZ(self, z: float) -> None:
        Logger.log(f"[VirtualTS] moveZ → {z}")
        self.z = z

    def moveXRel(self, x: float) -> None:
        self.x += x
        Logger.log(f"[VirtualTS] moveXRel {x:+} → {self.x}")

    def moveYRel(self, y: float) -> None:
        self.y += y
        Logger.log(f"[VirtualTS] moveYRel {y:+} → {self.y}")

    def moveZRel(self, z: float) -> None:
        self.z += z
        Logger.log(f"[VirtualTS] moveZRel {z:+} → {self.z}")

    def moveXYRel(self, x: float, y: float) -> None:
        self.x += x
        self.y += y
        Logger.log(f"[VirtualTS] moveXYRel ({x:+}, {y:+}) → ({self.x}, {self.y})")

    def moveXY(self, x: float, y: float) -> None:
        Logger.log(f"[VirtualTS] moveXY → ({x}, {y})")
        self.x = x
        self.y = y

    def posX(self) -> float:
        return self.x

    def posY(self) -> float:
        return self.y

    def posZ(self) -> float:
        return self.z

    def led_on(self) -> None:
        Logger.log("[VirtualTS] LED ON")

    def led_off(self) -> None:
        Logger.log("[VirtualTS] LED OFF")
