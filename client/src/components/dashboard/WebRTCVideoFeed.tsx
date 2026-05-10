import { useEffect, useLayoutEffect, useRef, useState } from "react";

interface WebRTCVideoFeedProps {
  host: string;
  cameraNumber: number;
  webrtcPort?: number;
  className?: string;
  onError?: (msg: string) => void;
  onConnected?: () => void;
}

const WebRTCVideoFeed = ({
  host,
  cameraNumber,
  webrtcPort = 3001,
  className,
  onError,
  onConnected,
}: WebRTCVideoFeedProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [status, setStatus] = useState<"connecting" | "live" | "error">("connecting");

  // Keep latest callbacks in refs so we can call them without re-running the
  // negotiation effect on every parent render (inline arrow callbacks would
  // otherwise change reference every render and tear down the PC).
  const onErrorRef = useRef(onError);
  const onConnectedRef = useRef(onConnected);
  useLayoutEffect(() => {
    onErrorRef.current = onError;
    onConnectedRef.current = onConnected;
  });

  useEffect(() => {
    let cancelled = false;
    const pc = new RTCPeerConnection({
      iceServers: [],
    });
    pcRef.current = pc;

    pc.addTransceiver("video", { direction: "recvonly" });

    pc.ontrack = (event) => {
      if (videoRef.current && event.streams[0]) {
        videoRef.current.srcObject = event.streams[0];
      }
    };

    pc.onconnectionstatechange = () => {
      if (cancelled) return;
      if (pc.connectionState === "connected") {
        setStatus("live");
        onConnectedRef.current?.();
      } else if (pc.connectionState === "failed" || pc.connectionState === "disconnected") {
        setStatus("error");
        onErrorRef.current?.(`WebRTC ${pc.connectionState}`);
      }
    };

    const negotiate = async () => {
      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // Wait for ICE gathering to complete (simpler than trickle ICE for localhost).
        await new Promise<void>((resolve) => {
          if (pc.iceGatheringState === "complete") {
            resolve();
            return;
          }
          const check = () => {
            if (pc.iceGatheringState === "complete") {
              pc.removeEventListener("icegatheringstatechange", check);
              resolve();
            }
          };
          pc.addEventListener("icegatheringstatechange", check);
        });

        if (cancelled) return;

        const local = pc.localDescription;
        if (!local) throw new Error("No local description");

        const url = `http://${host}:${webrtcPort}/offer/${cameraNumber}`;
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sdp: local.sdp, type: local.type }),
        });
        if (!resp.ok) throw new Error(`Server responded ${resp.status}`);
        const answer = await resp.json();
        if (cancelled) return;
        await pc.setRemoteDescription(answer);
      } catch (err) {
        if (!cancelled) {
          console.error("[WebRTC] negotiation failed:", err);
          setStatus("error");
          onErrorRef.current?.(err instanceof Error ? err.message : String(err));
        }
      }
    };

    negotiate();

    return () => {
      cancelled = true;
      pc.getSenders().forEach((s) => s.track?.stop());
      pc.close();
      pcRef.current = null;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, [host, cameraNumber, webrtcPort]);

  return (
    <div className={`relative w-full h-full ${className ?? ""}`}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }}
      />
      {status !== "live" && (
        <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded-full">
          {status === "connecting" ? "Connecting..." : "Connection error"}
        </div>
      )}
    </div>
  );
};

export default WebRTCVideoFeed;
