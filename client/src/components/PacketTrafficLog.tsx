import React, { useEffect, useState } from 'react';
import { useRecoilState, useRecoilValue } from 'recoil';
import { PacketTrafficLog, packetTrafficLogsAtom } from '../state/packetTrafficState';
import { PacketManager } from '../packets/PacketHandler';
import { jsonStateAtom } from '../state/jsonState';

interface PacketTrafficLogProps {
  maxEntries?: number;
}

const PacketTrafficLogComponent: React.FC<PacketTrafficLogProps> = ({ maxEntries = 100 }) => {
  const [packetLogs, setPacketLogs] = useRecoilState(packetTrafficLogsAtom);
  const jsonState = useRecoilValue(jsonStateAtom);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState('');
  const logContainerRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Register listener for packet traffic
    const unsubscribe = PacketManager.registerTrafficListener((packetInfo) => {
      setPacketLogs((prevLogs) => {
        const newLogs = [...prevLogs, {
          timestamp: packetInfo.timestamp,
          type: packetInfo.type,
          data: packetInfo.data,
          size: packetInfo.size,
          rawData: jsonState.lastRawMessage // Add raw message data
        }];
        
        // Limit the number of logs to prevent memory issues
        if (newLogs.length > maxEntries) {
          return newLogs.slice(newLogs.length - maxEntries);
        }
        return newLogs;
      });
    });

    // Cleanup listener on component unmount
    return () => {
      unsubscribe();
    };
  }, [setPacketLogs, maxEntries, jsonState.lastRawMessage]);

  // Auto-scroll to bottom when new logs are added
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [packetLogs, autoScroll]);

  // Format timestamp to readable format
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString() + '.' + date.getMilliseconds().toString().padStart(3, '0');
  };

  // Filter logs based on search term
  const filteredLogs = filter
    ? packetLogs.filter(log => 
        log.type.toLowerCase().includes(filter.toLowerCase()) || 
        JSON.stringify(log.data).toLowerCase().includes(filter.toLowerCase()) ||
        (log.rawData && log.rawData.toLowerCase().includes(filter.toLowerCase()))
      )
    : packetLogs;

  return (
    <div className="bg-gray-800 text-white p-4 rounded-lg shadow-lg flex flex-col h-full">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-xl font-bold">Incoming Packet Traffic</h2>
        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Filter packets..."
            className="bg-gray-700 text-white px-2 py-1 rounded text-sm"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={() => setAutoScroll(!autoScroll)}
              className="mr-1"
            />
            Auto-scroll
          </label>
          <button
            onClick={() => setPacketLogs([])}
            className="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-sm"
          >
            Clear
          </button>
        </div>
      </div>
      
      <div 
        ref={logContainerRef}
        className="flex-1 overflow-y-auto font-mono text-sm"
        style={{ maxHeight: 'calc(100% - 2rem)' }}
      >
        <table className="w-full border-collapse">
          <thead className="sticky top-0 bg-gray-900">
            <tr>
              <th className="text-left p-1 border-b border-gray-700">Time</th>
              <th className="text-left p-1 border-b border-gray-700">Type</th>
              <th className="text-left p-1 border-b border-gray-700">Size</th>
              <th className="text-left p-1 border-b border-gray-700">Data</th>
              <th className="text-left p-1 border-b border-gray-700">Raw String</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.map((log, index) => (
              <tr key={index} className="hover:bg-gray-700">
                <td className="p-1 border-b border-gray-700 whitespace-nowrap">{formatTimestamp(log.timestamp)}</td>
                <td className="p-1 border-b border-gray-700 whitespace-nowrap">{log.type}</td>
                <td className="p-1 border-b border-gray-700 whitespace-nowrap">{log.size} bytes</td>
                <td className="p-1 border-b border-gray-700 overflow-hidden text-ellipsis">
                  <pre className="whitespace-pre-wrap break-all max-w-xs">
                    {JSON.stringify(log.data, null, 2)}
                  </pre>
                </td>
                <td className="p-1 border-b border-gray-700 overflow-hidden text-ellipsis">
                  <pre className="whitespace-pre-wrap break-all max-w-xs">
                    {log.rawData || "N/A"}
                  </pre>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-2 text-sm text-gray-400">
        {filteredLogs.length} {filteredLogs.length === 1 ? 'packet' : 'packets'} logged
      </div>
    </div>
  );
};

export default PacketTrafficLogComponent; 