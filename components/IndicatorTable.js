// ./components/IndicatorTable.js
const { useState } = React;

// Helper functions (can be moved to a utils.js if they grow)
const getStatusColor = (indicator, value) => {
    if (value === null || typeof value === 'undefined' || isNaN(value)) return 'bg-gray-100 text-gray-800'; // Default for N/A
    if (indicator === 'williamsR') {
      return value >= -20 ? 'bg-red-100 text-red-800' :
             value >= -50 ? 'bg-yellow-100 text-yellow-800' :
             'bg-green-100 text-green-800';
    } else if (indicator === 'crsi') {
      return value >= 90 ? 'bg-red-100 text-red-800' :
             value >= 50 ? 'bg-yellow-100 text-yellow-800' :
             'bg-green-100 text-green-800';
    } else if (indicator === 'stochRsi') {
      return value >= 80 ? 'bg-red-100 text-red-800' :
             value >= 50 ? 'bg-yellow-100 text-yellow-800' :
             'bg-green-100 text-green-800';
    } else { // Default for rsi, mfi, adaptiveRsi, rvi (using 70 as general overbought threshold)
             // RVI's specific threshold is 0.7, but for color coding this generic check might be okay, or add specific RVI case.
      return value >= 70 ? 'bg-red-100 text-red-800' :
             value >= 50 ? 'bg-yellow-100 text-yellow-800' :
             'bg-green-100 text-green-800';
    }
};

const getTooltip = (indicator) => {
    const tooltips = {
      rsi: "Relative Strength Index - Overbought above 70, extreme above 80",
      stochRsi: "Stochastic RSI - Overbought above 80",
      mfi: "Money Flow Index - Overbought above 70, extreme above 80",
      crsi: "Connors RSI - Overbought above 90",
      williamsR: "Williams %R - Overbought above -20",
      rvi: "Relative Vigor Index - Overbought above 0.7 (bullish vigor)",
      adaptiveRsi: "Adaptive RSI - Overbought above 70"
    };
    return tooltips[indicator] || "";
};

const getIndicatorDescription = (indicator) => {
    const descriptions = {
      rsi: "The classic momentum oscillator that measures the speed and change of price movements. RSI is the foundation of many other indicators but can lag during strong trends.",
      stochRsi: "Applies the Stochastic oscillator formula to RSI values instead of price, making it more responsive to changes in momentum. Provides earlier signals than standard RSI.",
      mfi: "Similar to RSI but incorporates volume, making it useful for confirming price movements with volume support. Helps identify divergences between price and volume.",
      crsi: "Combines three different momentum measurements (price RSI, streak RSI, and percentile rank) for a more comprehensive view of market conditions. More sensitive to short-term changes.",
      williamsR: "Identifies overbought and oversold levels with a focus on price extremes relative to recent ranges. Often leads other indicators in signaling reversals.",
      rvi: "Measures the conviction of a price movement by comparing closing prices to opening prices. Helps distinguish between strong and weak trends based on intrabar behavior.",
      adaptiveRsi: "Adjusts to market volatility, becoming more responsive during volatile periods and more stable during quiet periods. Reduces false signals in changing market conditions."
    };
    return descriptions[indicator] || "";
};

const formatIndicatorName = (name) => {
    const names = {
      rsi: "RSI",
      stochRsi: "Stochastic RSI (%K)",
      mfi: "MFI",
      crsi: "Connors RSI",
      williamsR: "Williams %R",
      rvi: "RVI",
      adaptiveRsi: "Adaptive RSI"
    };
    return names[name] || name;
};

const isNumericAndNotNaN = (value) => typeof value === 'number' && !isNaN(value);

function IndicatorTable({ indicators }) {
  const [indicatorTableOpen, setIndicatorTableOpen] = useState(true); // Default to open for easier debugging

  if (!indicators || typeof indicators !== 'object' || Object.keys(indicators).length === 0) {
    // console.debug("IndicatorTable: 'indicators' prop is null, not an object, or empty. Not rendering table.");
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 flex justify-between items-center border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Technical Indicators</h3>
        <button
          onClick={() => setIndicatorTableOpen(!indicatorTableOpen)}
          className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm font-medium text-gray-700"
        >
          {indicatorTableOpen ? 'Hide Details' : 'Show Details'}
        </button>
      </div>

      {indicatorTableOpen && (
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Indicator</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monthly Value</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Weekly Value</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {Object.keys(indicators).map(indicatorKey => {
              const indicatorData = indicators[indicatorKey]; // This might be {'monthly': null, 'weekly': 75}

              const monthlyRawValue = indicatorData ? indicatorData.monthly : null;
              const weeklyRawValue = indicatorData ? indicatorData.weekly : null;

              const monthlyDisplayValue = isNumericAndNotNaN(monthlyRawValue)
                                  ? (indicatorKey === 'williamsR' || indicatorKey === 'rvi' ? monthlyRawValue.toFixed(2) : monthlyRawValue.toFixed(0))
                                  : "N/A";
              
              const weeklyDisplayValue = isNumericAndNotNaN(weeklyRawValue)
                                ? (indicatorKey === 'williamsR' || indicatorKey === 'rvi' ? weeklyRawValue.toFixed(2) : weeklyRawValue.toFixed(0))
                                : "N/A";
              
              // For status color, pass the raw value or a value that won't cause error in getStatusColor
              const monthlyStatusColorVal = isNumericAndNotNaN(monthlyRawValue) ? monthlyRawValue : null;
              const weeklyStatusColorVal = isNumericAndNotNaN(weeklyRawValue) ? weeklyRawValue : null;

              const getStatusText = (value, key) => {
                if (!isNumericAndNotNaN(value)) return 'N/A';
                // Define thresholds for "Overbought" based on the indicator key
                let overboughtThreshold = 70; // Default
                if (key === 'stochRsi') overboughtThreshold = 80;
                else if (key === 'crsi') overboughtThreshold = 90;
                else if (key === 'williamsR') overboughtThreshold = -20;
                // For RVI, threshold is 0.7, but comparison needs to be adjusted for "higher is more overbought"
                // Let's stick to the general logic for now unless RVI needs special text

                if (key === 'williamsR') {
                    return value >= overboughtThreshold ? 'Overbought' : 'Normal';
                }
                return value >= overboughtThreshold ? 'Overbought' : 'Normal';
              };

              return (
                <tr key={indicatorKey}>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">{formatIndicatorName(indicatorKey)}</div>
                        <div className="ml-2 text-gray-400 cursor-help" title={getTooltip(indicatorKey)}>ⓘ</div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1 max-w-md">{getIndicatorDescription(indicatorKey)}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{monthlyDisplayValue}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{weeklyDisplayValue}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col space-y-1">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(indicatorKey, monthlyStatusColorVal)}`}>
                          M: {getStatusText(monthlyStatusColorVal, indicatorKey)}
                        </span>
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(indicatorKey, weeklyStatusColorVal)}`}>
                          W: {getStatusText(weeklyStatusColorVal, indicatorKey)}
                        </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}