import { useEffect, useMemo, useState } from "react";
import { useRecoilValue } from "recoil";
import { useSendJSON } from "../../hooks/useSendJSON";
import { positionSettingsAtom } from "../../state/appState";

interface TraceOverAreaStatus {
  success: boolean;
  message: string;
}

const TraceOverAreaBox = () => {
  const sendJson = useSendJSON();
  const positionSettings = useRecoilValue(positionSettingsAtom);

  const [waferId, setWaferId] = useState<string>("1");
  const [startX, setStartX] = useState<string>("");
  const [startY, setStartY] = useState<string>("");
  const [startZ, setStartZ] = useState<string>("");
  const [endX, setEndX] = useState<string>("");
  const [endY, setEndY] = useState<string>("");
  const [magnification, setMagnification] = useState<number>(20);
  const [initialWaitTime, setInitialWaitTime] = useState<number>(25);
  const [cameraIndex, setCameraIndex] = useState<number>(0);
  const [saveImages, setSaveImages] = useState<boolean>(true);
  const [status, setStatus] = useState<TraceOverAreaStatus | null>(null);

  useEffect(() => {
    if (!status) {
      return;
    }

    const timer = window.setTimeout(() => {
      setStatus(null);
    }, 4000);

    return () => window.clearTimeout(timer);
  }, [status]);

  const jsonPreview = useMemo(() => {
    const payload = {
      type: "EXECUTE_TRANSFER_FUNCTION",
      transfer_function_name: "RUN_TRACE_OVER_AREA",
      parameters: [
        {
          wafer_id: waferId,
          start_x: startX === "" ? "" : Number(startX),
          start_y: startY === "" ? "" : Number(startY),
          start_z: startZ === "" ? "" : Number(startZ),
          end_x: endX === "" ? "" : Number(endX),
          end_y: endY === "" ? "" : Number(endY),
          magnification,
          initial_wait_time: initialWaitTime,
          camera_index: cameraIndex,
          save_images: saveImages,
        },
      ],
    };

    return JSON.stringify(payload, null, 2);
  }, [waferId, startX, startY, startZ, endX, endY, magnification, initialWaitTime, cameraIndex, saveImages]);

  const isCoordinateValid = (value: string): boolean => value !== "" && !Number.isNaN(Number(value));

  const copyCurrentToStart = () => {
    const pos = positionSettings.currentPosition;
    if (!pos) {
      setStatus({ success: false, message: "Current position is unavailable." });
      return;
    }
    setStartX(pos.x.toFixed(3));
    setStartY(pos.y.toFixed(3));
    setStartZ((pos.z ?? 0).toFixed(3));
  };

  const copyCurrentToEnd = () => {
    const pos = positionSettings.currentPosition;
    if (!pos) {
      setStatus({ success: false, message: "Current position is unavailable." });
      return;
    }
    setEndX(pos.x.toFixed(3));
    setEndY(pos.y.toFixed(3));
  };

  const handleRun = () => {
    const valid = [startX, startY, startZ, endX, endY].every(isCoordinateValid);
    if (!valid) {
      setStatus({ success: false, message: "Please provide valid start/end coordinates." });
      return;
    }

    const data = {
      type: "EXECUTE_TRANSFER_FUNCTION",
      transfer_function_name: "RUN_TRACE_OVER_AREA",
      parameters: JSON.stringify([
        {
          wafer_id: waferId,
          start_x: Number(startX),
          start_y: Number(startY),
          start_z: Number(startZ),
          end_x: Number(endX),
          end_y: Number(endY),
          magnification,
          initial_wait_time: initialWaitTime,
          camera_index: cameraIndex,
          save_images: saveImages,
        },
      ]),
    };

    sendJson(data);
    setStatus({ success: true, message: "RUN_TRACE_OVER_AREA command sent." });
  };

  return (
    <div className="trace-over-box">
      <div className="grid grid-cols-2 gap-2 mb-2">
        <label className="text-sm text-left">
          Wafer ID
          <input
            className="w-full p-1 border rounded"
            value={waferId}
            onChange={(e) => setWaferId(e.target.value)}
          />
        </label>
        <label className="text-sm text-left">
          Magnification
          <select
            className="w-full p-1 border rounded"
            value={magnification}
            onChange={(e) => setMagnification(Number(e.target.value))}
          >
            <option value={5}>5x</option>
            <option value={10}>10x</option>
            <option value={20}>20x</option>
            <option value={40}>40x</option>
            <option value={50}>50x</option>
            <option value={100}>100x</option>
          </select>
        </label>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-2">
        <label className="text-sm text-left">
          Start X
          <input className="w-full p-1 border rounded" value={startX} onChange={(e) => setStartX(e.target.value)} />
        </label>
        <label className="text-sm text-left">
          Start Y
          <input className="w-full p-1 border rounded" value={startY} onChange={(e) => setStartY(e.target.value)} />
        </label>
        <label className="text-sm text-left">
          Start Z
          <input className="w-full p-1 border rounded" value={startZ} onChange={(e) => setStartZ(e.target.value)} />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2">
        <label className="text-sm text-left">
          End X
          <input className="w-full p-1 border rounded" value={endX} onChange={(e) => setEndX(e.target.value)} />
        </label>
        <label className="text-sm text-left">
          End Y
          <input className="w-full p-1 border rounded" value={endY} onChange={(e) => setEndY(e.target.value)} />
        </label>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-2 items-end">
        <label className="text-sm text-left">
          Initial Wait (s)
          <input
            type="number"
            min={0}
            step={0.5}
            className="w-full p-1 border rounded"
            value={initialWaitTime}
            onChange={(e) => setInitialWaitTime(Math.max(0, Number(e.target.value) || 0))}
          />
        </label>
        <label className="text-sm text-left">
          Camera Index
          <input
            type="number"
            min={0}
            className="w-full p-1 border rounded"
            value={cameraIndex}
            onChange={(e) => setCameraIndex(Math.max(0, Number(e.target.value) || 0))}
          />
        </label>
        <label className="text-sm text-left flex items-center gap-2 pb-1">
          <input type="checkbox" checked={saveImages} onChange={(e) => setSaveImages(e.target.checked)} />
          Save Images
        </label>
      </div>

      <div className="flex gap-2 mb-2">
        <button className="trace-button" onClick={copyCurrentToStart}>Copy Current to Start</button>
        <button className="trace-button" onClick={copyCurrentToEnd}>Copy Current to End</button>
        <button className="trace-button" onClick={handleRun}>Run</button>
      </div>

      {status && (
        <p className={`text-sm text-left ${status.success ? "text-green-600" : "text-red-600"}`}>
          {status.message}
        </p>
      )}

      <textarea
        className="w-full p-2 border rounded text-xs font-mono"
        rows={8}
        value={jsonPreview}
        readOnly
      />
    </div>
  );
};

export default TraceOverAreaBox;
