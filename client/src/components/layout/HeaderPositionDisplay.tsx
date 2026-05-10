import { useRecoilState } from "recoil";
import { positionSettingsAtom } from "../../state/appState";

const HeaderPositionDisplay = () => {
  const [positionSettings, setPositionSettings] = useRecoilState(positionSettingsAtom);
  const { autoUpdate, pollRate, currentPosition: position } = positionSettings;

  const setAutoUpdate = (value: boolean) => {
    setPositionSettings(prev => ({ ...prev, autoUpdate: value }));
  };

  const setPollRate = (value: number) => {
    setPositionSettings(prev => ({ ...prev, pollRate: value }));
  };

  const getPollInterval = () => {
    const safeRate = Math.max(0.1, Math.min(50, pollRate));
    return Math.round(1000 / safeRate);
  };

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
    <div className="header-position-display">
      <div className="header-position-polling">
        <label className="flex items-center text-xs mr-2">
          <input
            type="checkbox"
            checked={autoUpdate}
            onChange={() => setAutoUpdate(!autoUpdate)}
            className="mr-1 h-3 w-3"
          />
          <span className="whitespace-nowrap">Auto</span>
        </label>
        
        <div className="header-poll-rate">
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
      
      <div className="position-values">
        <div className="position-axis-value">
          <span className="font-medium mr-1">X:</span>
          <span>
            {position ? formatPosition(position.x) : "0.000"}
          </span>
        </div>
        <div className="position-axis-value">
          <span className="font-medium mr-1">Y:</span>
          <span>
            {position ? formatPosition(position.y) : "0.000"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default HeaderPositionDisplay; 
