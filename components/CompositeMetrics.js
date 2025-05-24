// ./components/CompositeMetrics.js
function CompositeMetrics({ metrics }) {
  if (!metrics) return null;

  const ProgressBar = ({ value, type }) => {
    const colorClass = value > 75 ? 'bg-red-500' : value > 50 ? 'bg-yellow-500' : 'bg-green-500';
    const displayValue = type === 'percentage' ? `${value.toFixed(1)}%` : value.toFixed(1);
    return (
      <React.Fragment>
        <div className="flex mb-2 items-center justify-between">
          <div>
            <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-blue-600 bg-blue-200">
              {type === 'cos' ? 'Monthly' : 'Monthly'} 
            </span>
          </div>
          <div className="text-right">
            <span className="text-xs font-semibold inline-block text-blue-600">
              {displayValue}
            </span>
          </div>
        </div>
        <div className="overflow-hidden h-2 mb-2 text-xs flex rounded bg-gray-200">
          <div style={{ width: `${Math.min(100, value)}%` }}
               className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${colorClass}`}>
          </div>
        </div>
      </React.Fragment>
    );
  };


  return (
    <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Composite Overbought Score (COS)
          <span className="ml-2 text-gray-400 cursor-help" title="Composite Overbought Score - Combines all indicators with weighted importance. Values above 75 suggest extreme overbought conditions.">ⓘ</span>
        </h3>
        <div className="relative pt-1">
            <ProgressBar value={metrics.cos.monthly} type="cos" />
            <div className="flex mb-2 items-center justify-between mt-3"> {/* Added mt-3 for spacing */}
                <div>
                    <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-blue-600 bg-blue-200">
                        Weekly
                    </span>
                </div>
                <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-blue-600">
                        {metrics.cos.weekly.toFixed(1)}
                    </span>
                </div>
            </div>
            <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-200">
                <div
                style={{ width: `${Math.min(100, metrics.cos.weekly)}%` }}
                className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${
                    metrics.cos.weekly > 75
                    ? 'bg-red-500'
                    : metrics.cos.weekly > 50
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                }`}
                ></div>
            </div>
          <p className="text-sm text-gray-600">
            COS combines all indicators with weighted importance. Values above 75 suggest extreme overbought conditions.
          </p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Bull Strength Index (BSI)
          <span className="ml-2 text-gray-400 cursor-help" title="Bull Strength Index - Measures the strength of the bullish trend. Values above 75% indicate a strong bullish trend, 50-75% a moderate trend, and below 50% a weak or bearish trend.">ⓘ</span>
        </h3>
        <div className="relative pt-1">
          <ProgressBar value={metrics.bsi.monthly} type="percentage" />
          <div className="flex mb-2 items-center justify-between mt-3"> {/* Added mt-3 for spacing */}
            <div>
                <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-blue-600 bg-blue-200">
                    Weekly
                </span>
            </div>
            <div className="text-right">
                <span className="text-xs font-semibold inline-block text-blue-600">
                    {metrics.bsi.weekly.toFixed(1) + '%'}
                </span>
            </div>
          </div>
          <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-200">
            <div
            style={{ width: `${Math.min(100, metrics.bsi.weekly)}%` }}
            className={`shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center ${
                metrics.bsi.weekly > 75
                ? 'bg-red-500'
                : metrics.bsi.weekly > 50
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
            }`}
            ></div>
          </div>
          <p className="text-sm text-gray-600">
            BSI measures the strength of the bullish trend. Values above 75% indicate a strong bullish trend, 50-75% a moderate trend, and below 50% a weak or bearish trend.
          </p>
        </div>
      </div>
    </div>
  );
}