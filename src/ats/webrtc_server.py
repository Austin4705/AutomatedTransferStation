"""WebRTC video streaming server.

Runs an aiohttp + aiortc app on a dedicated port (default 3001) so the
existing sync Flask server on port 3000 can keep serving MJPEG, snapshots,
and dashboard config unchanged.

Client signaling: POST /offer/{camera_id} with {"sdp": "...", "type": "offer"}
returns {"sdp": "...", "type": "answer"}.
"""
from __future__ import annotations

import asyncio
import fractions
import os
import re
import time
from typing import Set

import cv2
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCRtpSender,
    RTCSessionDescription,
)
from aiortc.mediastreams import MediaStreamTrack
from av import VideoFrame

from .camera import Camera
from .algorithms import pipeline as algo_pipeline


_pcs: Set[RTCPeerConnection] = set()
_VIDEO_CLOCK_RATE = 90000
_VIDEO_TIME_BASE = fractions.Fraction(1, _VIDEO_CLOCK_RATE)


def _bitrate_kbps() -> int:
    try:
        return int(os.getenv("WEBRTC_BITRATE_KBPS", "50000"))
    except ValueError:
        return 50000


def _target_fps() -> float:
    try:
        return float(os.getenv("WEBRTC_FPS", "30"))
    except ValueError:
        return 30.0


class CameraVideoTrack(MediaStreamTrack):
    """A WebRTC video track that pulls frames from a Camera instance.

    Overlays (whitebalance, FPS counter, crosshair) match
    Camera.get_single_frame_as_response so the WebRTC view is visually
    equivalent to the MJPEG view.
    """

    kind = "video"

    def __init__(self, camera_id: int):
        super().__init__()
        self.camera_id = camera_id
        self._start_wall: float | None = None
        self._frame_period = 1.0 / max(_target_fps(), 1.0)
        self._next_send: float | None = None

    async def recv(self) -> VideoFrame:
        now = time.time()
        if self._next_send is None:
            self._start_wall = now
            self._next_send = now
        else:
            wait = self._next_send - now
            if wait > 0:
                await asyncio.sleep(wait)
        self._next_send += self._frame_period

        camera = Camera.global_list.get(self.camera_id)
        if camera is None:
            # Camera disappeared — emit a black frame to keep the track alive.
            import numpy as np
            frame_bgr = np.zeros((480, 640, 3), dtype=np.uint8)
        else:
            frame_bgr = camera.get_frame()
            if camera.whitebalance_enabled:
                frame_bgr = algo_pipeline.apply_pipeline("live_view", frame_bgr.copy())
            if camera.fps_counter_enabled:
                with camera._fps_lock:
                    fps_display = camera.fps_display
                    fps_total = camera.fps_total
                    frame_count = camera.frame_count
                cv2.putText(frame_bgr, f"FPS: {fps_display:.1f}, Total: {fps_total:.1f}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame_bgr, f"Frame: {frame_count}",
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                h, w = frame_bgr.shape[:2]
                cx, cy = w // 2, h // 2
                cv2.line(frame_bgr, (cx - 20, cy), (cx + 20, cy), (0, 0, 255), 2)
                cv2.line(frame_bgr, (cx, cy - 20), (cx, cy + 20), (0, 0, 255), 2)

        video_frame = VideoFrame.from_ndarray(frame_bgr, format="bgr24")
        elapsed = (self._next_send - self._frame_period) - (self._start_wall or now)
        video_frame.pts = int(elapsed * _VIDEO_CLOCK_RATE)
        video_frame.time_base = _VIDEO_TIME_BASE
        return video_frame


def _force_codec(pc: RTCPeerConnection, sender: RTCRtpSender, codec_mime: str) -> None:
    """Restrict the sender's codec preferences to a single codec (e.g. VP8)."""
    capabilities = RTCRtpSender.getCapabilities("video")
    if not capabilities:
        return
    preferred = [c for c in capabilities.codecs if c.mimeType.lower() == codec_mime.lower()]
    if not preferred:
        return
    transceiver = next(
        (t for t in pc.getTransceivers() if t.sender is sender), None
    )
    if transceiver is not None:
        transceiver.setCodecPreferences(preferred)


_MDNS_CANDIDATE_RE = re.compile(
    r"(a=candidate:\S+\s+\S+\s+\S+\s+\S+\s+)([0-9a-f]+(?:-[0-9a-f]+)*\.local)(\s)",
    re.IGNORECASE,
)


def _rewrite_mdns_candidates(sdp: str, replacement: str = "127.0.0.1") -> str:
    """Replace mDNS .local candidate hostnames with a routable address.

    Modern browsers (Firefox always, Chrome on https) obfuscate local IPs as
    <uuid>.local for privacy. aiortc/aioice can in principle resolve these via
    multicast DNS, but that is unreliable on macOS where mDNSResponder owns
    UDP/5353. For the localhost-only setup this app targets, rewriting to
    127.0.0.1 lets ICE proceed without depending on mDNS at all (the browser's
    UDP socket is bound to 0.0.0.0 so loopback delivery works).

    Disable by setting WEBRTC_REWRITE_MDNS=0 (e.g. when connecting across a
    network — though that case has its own NAT considerations).
    """
    if os.getenv("WEBRTC_REWRITE_MDNS", "1") == "0":
        return sdp
    return _MDNS_CANDIDATE_RE.sub(rf"\g<1>{replacement}\g<3>", sdp)


def _bump_bitrate_in_sdp(sdp: str, kbps: int) -> str:
    """Inject b=AS:<kbps> into every video m-section."""
    out_lines = []
    in_video = False
    inserted = False
    for line in sdp.splitlines():
        out_lines.append(line)
        if line.startswith("m=video"):
            in_video = True
            inserted = False
            continue
        if in_video and not inserted and (line.startswith("c=") or line.startswith("a=")):
            if line.startswith("c="):
                out_lines.append(f"b=AS:{kbps}")
                inserted = True
        if line.startswith("m=") and not line.startswith("m=video"):
            in_video = False
    return "\r\n".join(out_lines) + "\r\n"


async def _set_encoder_bitrate_when_ready(sender: RTCRtpSender, bps: int) -> None:
    """aiortc has no public bitrate API; poke the private encoder once it's
    instantiated by the sender's RTP loop. The encoder is created lazily after
    the connection is up, so we poll briefly."""
    attr = "_RTCRtpSender__encoder"
    for _ in range(100):  # ~10s total
        encoder = getattr(sender, attr, None)
        if encoder is not None and hasattr(encoder, "target_bitrate"):
            encoder.target_bitrate = bps
            print(f"[webrtc] encoder target_bitrate set to {bps} bps")
            return
        await asyncio.sleep(0.1)
    print("[webrtc] gave up waiting for encoder; bitrate left at default")


async def _offer_handler(request: web.Request) -> web.Response:
    camera_id_raw = request.match_info["camera_id"]
    try:
        camera_id = int(camera_id_raw)
    except ValueError:
        return web.Response(status=400, text=f"Invalid camera_id: {camera_id_raw}")
    if camera_id not in Camera.global_list:
        return web.Response(status=404, text=f"Camera {camera_id} not found")

    params = await request.json()
    rewritten_offer_sdp = _rewrite_mdns_candidates(params["sdp"])
    offer = RTCSessionDescription(sdp=rewritten_offer_sdp, type=params["type"])

    pc = RTCPeerConnection()
    _pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_state_change():
        if pc.connectionState in ("failed", "closed"):
            await pc.close()
            _pcs.discard(pc)

    track = CameraVideoTrack(camera_id)
    sender = pc.addTrack(track)
    _force_codec(pc, sender, "video/VP8")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Schedule the encoder bitrate bump once aiortc has created the encoder.
    bps = _bitrate_kbps() * 1000
    asyncio.ensure_future(_set_encoder_bitrate_when_ready(sender, bps))

    # Send a munged SDP to the client so it advertises the higher bitrate;
    # aiortc strips b=AS when re-serializing, so we do this after
    # setLocalDescription rather than before.
    final_sdp = _bump_bitrate_in_sdp(pc.localDescription.sdp, _bitrate_kbps())

    return web.json_response({
        "sdp": final_sdp,
        "type": pc.localDescription.type,
    })


async def _on_shutdown(app: web.Application) -> None:
    coros = [pc.close() for pc in list(_pcs)]
    await asyncio.gather(*coros, return_exceptions=True)
    _pcs.clear()


def _build_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/offer/{camera_id}", _offer_handler)
    app.on_shutdown.append(_on_shutdown)
    return app


def _add_cors(app: web.Application) -> None:
    """Permissive CORS for browser clients on a different origin (vite dev server)."""
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        if request.method == "OPTIONS":
            resp = web.Response(status=204)
        else:
            try:
                resp = await handler(request)
            except web.HTTPException as ex:
                resp = ex
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    app.middlewares.append(cors_middleware)


def startup_webrtc_server() -> None:
    """Run the aiohttp+aiortc server. Call from a daemon thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = _build_app()
    _add_cors(app)

    port = int(os.environ.get("WEBRTC_PORT", "3001"))
    host = os.environ.get("WEBRTC_HOST", "0.0.0.0")
    print(f"Starting WebRTC server on {host}:{port} "
          f"(VP8, ~{_bitrate_kbps()} kbps cap, ~{_target_fps():.0f} fps)")

    runner = web.AppRunner(app, access_log=None)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host, port)
    loop.run_until_complete(site.start())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(runner.cleanup())
        loop.close()
