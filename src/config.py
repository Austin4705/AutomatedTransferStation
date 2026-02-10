"""
Pydantic configuration models for the Automated Transfer Station.

All configuration is loaded from environment variables (via .env files)
and validated at startup. Invalid configuration raises clear errors.
"""

from __future__ import annotations

import os
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TransferStationConfig(BaseModel):
    """Configuration for the transfer station hardware."""
    station_type: str = Field(default="virtual", description="Registered driver name")


class CameraConfig(BaseModel):
    """Configuration for camera hardware."""
    camera_type: str = Field(default="virtual", description="Registered driver name")
    max_cameras: int = Field(default=3, ge=1, le=10, description="Max cameras to probe")
    init_timeout: float = Field(default=3.0, ge=0.0, description="Seconds to wait after camera init")


class OmeroConfig(BaseModel):
    """Configuration for the OMERO image server."""
    host: str = Field(default="localhost")
    port: int = Field(default=4064, ge=1, le=65535)
    username: str = Field(default="root")
    password: str = Field(default="omero")


class NetworkConfig(BaseModel):
    """Configuration for network servers."""
    websocket_host: str = Field(default="0.0.0.0")
    websocket_port: int = Field(default=8765, ge=1, le=65535)
    flask_host: str = Field(default="0.0.0.0")
    flask_port: int = Field(default=3000, ge=1, le=65535)


class AppConfig(BaseModel):
    """Top-level application configuration — aggregates all sub-configs."""
    station: TransferStationConfig = Field(default_factory=TransferStationConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    omero: OmeroConfig = Field(default_factory=OmeroConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build an AppConfig from current os.environ (call after load_dotenv)."""
        return cls(
            station=TransferStationConfig(
                station_type=os.getenv("TRANSFER_STATION_TYPE", "virtual"),
            ),
            camera=CameraConfig(
                camera_type=os.getenv("CAMERA_TYPE", "virtual"),
                max_cameras=int(os.getenv("MAX_CAMERAS", "3")),
                init_timeout=float(os.getenv("CAMERA_INIT_TIMEOUT", "3")),
            ),
            omero=OmeroConfig(
                host=os.getenv("OMERO_HOST", "localhost"),
                port=int(os.getenv("OMERO_PORT", "4064")),
                username=os.getenv("OMERO_USERNAME", "root"),
                password=os.getenv("OMERO_PASSWORD", "omero"),
            ),
            network=NetworkConfig(
                websocket_host=os.getenv("WEBSOCKET_HOST", "0.0.0.0"),
                websocket_port=int(os.getenv("WEBSOCKET_PORT", "8765")),
                flask_host=os.getenv("FLASK_HOST", "0.0.0.0"),
                flask_port=int(os.getenv("FLASK_PORT", "3000")),
            ),
        )


# ─── Packet validation models ───────────────────────────────────────

class MovePacket(BaseModel):
    """Validates a movement command packet."""
    type: str
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class ExecuteTransferFunctionPacket(BaseModel):
    """Validates an EXECUTE_TRANSFER_FUNCTION packet."""
    type: Literal["EXECUTE_TRANSFER_FUNCTION"]
    transfer_function_name: str
    parameters: str  # JSON-encoded string of parameters


class SnapShotPacket(BaseModel):
    """Validates a SNAP_SHOT packet."""
    type: Literal["SNAP_SHOT", "SNAP_SHOT_FLAKE_HUNTED"]
    camera: int = Field(ge=0)


class TogglePacket(BaseModel):
    """Validates a toggle (whitebalance / FPS counter) packet."""
    type: str
    state: str = "off"
    camera_index: int = 0


class SetExposurePacket(BaseModel):
    """Validates a SET_EXPOSURE_TIME transfer function payload."""
    camera_index: int = Field(default=0, ge=0)
    exposure_time_us: int = Field(default=10000, ge=1)


