from typing import Dict, Callable

class BaseHandlers:
    """Base class for packet handlers"""
    packet_handlers: Dict[str, Callable] = {}

    @staticmethod
    def packet_handler(packet_type: str):
        """Decorator to register packet handlers"""
        def decorator(func):
            BaseHandlers.packet_handlers[packet_type] = func
            return func
        return decorator 