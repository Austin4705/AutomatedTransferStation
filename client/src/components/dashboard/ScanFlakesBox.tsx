import { useSendJSON } from "../../hooks/useSendJSON";
import { useState, useEffect } from "react";
import { useRecoilValue } from "recoil";
import { jsonStateAtom } from "../../state/jsonState";

interface CollectionConfig {
  key: string;
  collection_id: string;
  apply_whitebalance: boolean;
  wafer_type: "HBn" | "Graphene";
}

const ScanFlakesBox = () => {
  const sendJson = useSendJSON();
  const jsonState = useRecoilValue(jsonStateAtom);
  const [collectionCount, setCollectionCount] = useState<number>(1);
  const [collections, setCollections] = useState<CollectionConfig[]>([
    {
      key: "collection-0",
      collection_id: "",
      apply_whitebalance: false,
      wafer_type: "HBn"
    }
  ]);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error", message: string } | null>(null);

  // Update collections array when count changes
  useEffect(() => {
    setCollections(prev => {
      const newCollections = [...prev];

      // Add new collections if count increased
      while (newCollections.length < collectionCount) {
        newCollections.push({
          key: `collection-${newCollections.length}`,
          collection_id: "",
          apply_whitebalance: false,
          wafer_type: "HBn"
        });
      }

      // Remove collections if count decreased
      while (newCollections.length > collectionCount) {
        newCollections.pop();
      }

      return newCollections;
    });
  }, [collectionCount]);

  // Listen for response messages
  useEffect(() => {
    if (!jsonState.lastJsonMessage) return;

    const message = jsonState.lastJsonMessage as any;

    if (message.type === "SCAN_FLAKES_RESULT") {
      if (message.success) {
        setStatusMessage({
          type: "success",
          message: `Successfully scanned ${message.collectionCount || collectionCount} collection(s)`
        });
      } else {
        setStatusMessage({
          type: "error",
          message: message.message || "Failed to scan flakes"
        });
      }

      setTimeout(() => setStatusMessage(null), 5000);
    }
  }, [jsonState.lastJsonMessage, collectionCount]);

  const handleCollectionIdChange = (index: number, value: string) => {
    setCollections(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], collection_id: value };
      return updated;
    });
  };

  const handleWhitebalanceChange = (index: number, checked: boolean) => {
    setCollections(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], apply_whitebalance: checked };
      return updated;
    });
  };

  const handleWaferTypeChange = (index: number, value: "HBn" | "Graphene") => {
    setCollections(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], wafer_type: value };
      return updated;
    });
  };

  const handleScanFlakes = () => {
    // Validate all collection IDs are filled
    for (let i = 0; i < collections.length; i++) {
      if (!collections[i].collection_id) {
        alert(`Please enter Collection ID for collection ${i + 1}`);
        return;
      }
    }

    // Build config object
    const scanFlakesConfig = {
      collections: collections.map(c => ({
        collection_id: c.collection_id,
        apply_whitebalance: c.apply_whitebalance,
        wafer_type: c.wafer_type
      }))
    };

    const data = {
      type: "SCAN_FLAKES",
      parameters: JSON.stringify(scanFlakesConfig)
    };

    sendJson(data);
  };

  return (
    <div className="scan-flakes-box p-4 bg-white rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-3">Scan Flakes</h3>

      {/* Status Message */}
      {statusMessage && (
        <div className={`mb-3 p-2 rounded ${
          statusMessage.type === "success"
            ? "bg-green-100 text-green-800"
            : "bg-red-100 text-red-800"
        }`}>
          {statusMessage.message}
        </div>
      )}

      {/* Collection Count */}
      <div className="mb-4">
        <label className="text-sm font-medium mr-2">Number of Collections:</label>
        <input
          type="number"
          min="1"
          value={collectionCount}
          onChange={(e) => setCollectionCount(Math.max(1, parseInt(e.target.value) || 1))}
          className="p-1 border rounded w-20 text-sm"
        />
      </div>

      {/* Collections Table */}
      <div className="overflow-x-auto mb-4">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2">#</th>
              <th className="border p-2">Collection ID</th>
              <th className="border p-2">Apply Whitebalance</th>
              <th className="border p-2">Wafer Type</th>
            </tr>
          </thead>
          <tbody>
            {collections.map((collection, index) => (
              <tr key={collection.key}>
                <td className="border p-2 text-center">{index + 1}</td>
                <td className="border p-2">
                  <input
                    type="text"
                    value={collection.collection_id}
                    onChange={(e) => handleCollectionIdChange(index, e.target.value)}
                    className="w-full p-1 border rounded text-xs"
                    placeholder="Enter collection ID"
                  />
                </td>
                <td className="border p-2 text-center">
                  <input
                    type="checkbox"
                    checked={collection.apply_whitebalance}
                    onChange={(e) => handleWhitebalanceChange(index, e.target.checked)}
                    className="form-checkbox h-4 w-4"
                  />
                </td>
                <td className="border p-2">
                  <select
                    value={collection.wafer_type}
                    onChange={(e) => handleWaferTypeChange(index, e.target.value as "HBn" | "Graphene")}
                    className="w-full p-1 border rounded text-xs"
                  >
                    <option value="HBn">HBn</option>
                    <option value="Graphene">Graphene</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Scan Button */}
      <div className="flex justify-center">
        <button
          onClick={handleScanFlakes}
          className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded font-medium"
        >
          Scan Flakes
        </button>
      </div>
    </div>
  );
};

export default ScanFlakesBox;
