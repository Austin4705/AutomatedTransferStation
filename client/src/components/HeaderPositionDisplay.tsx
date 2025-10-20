import { usePositionContext } from "../state/positionContext";

const HeaderPositionDisplay = () => {
  const { 
    autoUpdate, 
    setAutoUpdate, 
    pollRate, 
    setPollRate, 
    position, 
    isLoading 
  } = usePositionContext();

  // Calculate polling interval in milliseconds
  const getPollInterval = () => {
    const safeRate = Math.max(0.1, Math.min(50, pollRate));
    return Math.round(1000 / safeRate);
  };

  // Handle poll rate change
  const handlePollRateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    if (!isNaN(value) && value > 0) {
      setPollRate(value);
    }
  };

  const formatPosition = (value: number | undefined): string => {
    if (value === undefined) return "0.000";
    return value.toFixed(3);
  };

  return (
    <div className="header-position-display flex items-center ml-4">
      <div className="flex items-center mr-3">
        <label className="flex items-center text-xs mr-2">
          <input
            type="checkbox"
            checked={autoUpdate}
            onChange={() => setAutoUpdate(!autoUpdate)}
            className="mr-1 h-3 w-3"
          />
          <span className="whitespace-nowrap">Auto</span>
        </label>
        
        <div className="flex items-center">
          <input
            type="number"
            min="0.1"
            max="50"
            step="0.1"
            value={pollRate.toFixed(1)}
            onChange={handlePollRateChange}
            disabled={!autoUpdate}
            className="w-10 h-5 text-xs px-1"
          />
          <span className="text-xs ml-1 whitespace-nowrap">
            Hz <span className="text-gray-300">({getPollInterval()}ms)</span>
          </span>
        </div>
      </div>
      
      <div className="position-values flex items-center text-xs">
        <div className="flex items-center mr-2">
          <span className="font-medium mr-1">X:</span>
          <span className={`${isLoading ? 'opacity-50' : ''}`}>
            {position ? formatPosition(position.x) : "0.000"}
          </span>
        </div>
        <div className="flex items-center">
          <span className="font-medium mr-1">Y:</span>
          <span className={`${isLoading ? 'opacity-50' : ''}`}>
            {position ? formatPosition(position.y) : "0.000"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default HeaderPositionDisplay; 