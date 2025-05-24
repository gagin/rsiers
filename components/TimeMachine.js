// ./components/TimeMachine.js
const { useState, useEffect, useRef } = React;

function TimeMachine({
  timeMachineData,
  selectedTimePoint,
  timeMachineActive,
  selectedDate,
  onActivateTimeMachine,
  onFetchDataForDate,
  datePickerRef, // Pass the ref from App.js
  compositeMetrics // Pass current composite metrics for comparison display
}) {
  const [historicalTableOpen, setHistoricalTableOpen] = useState(false);

  useEffect(() => {
    // Ensure datePickerRef.current exists and flatpickr hasn't been initialized on it yet
    if (datePickerRef.current && !datePickerRef.current._flatpickrInstance) {
      const fp = flatpickr(datePickerRef.current, {
        dateFormat: "Y-m-d",
        maxDate: "today",
        minDate: "2017-01-01", // <<< HARD LIMIT SET HERE
        onChange: function(selectedDates, dateStr) {
          if (selectedDates.length > 0) {
            const date = selectedDates[0];
            console.log("Date selected in TimeMachine component:", date, dateStr);
            onFetchDataForDate(date); // Call prop function from App.js
          }
        }
      });
      // Store the instance on the ref's current property to access/destroy later
      datePickerRef.current._flatpickrInstance = fp; 

      // Cleanup function to destroy flatpickr instance when component unmounts
      // or when datePickerRef changes (though it shouldn't change often)
      return () => {
        if (datePickerRef.current && datePickerRef.current._flatpickrInstance) {
            datePickerRef.current._flatpickrInstance.destroy();
            // Important to remove the stored instance to allow re-initialization if needed
            delete datePickerRef.current._flatpickrInstance; 
        }
      };
    }
  }, [datePickerRef, onFetchDataForDate]); // Dependencies for this effect

  // Effect to update calendar when selectedTimePoint or selectedDate changes externally
  // (e.g., clicking a historical event or exiting time machine)
  useEffect(() => {
    if (datePickerRef.current && datePickerRef.current._flatpickrInstance) {
        if (selectedTimePoint && selectedTimePoint.date) {
            // Set date without triggering onChange, to reflect the active time point
            datePickerRef.current._flatpickrInstance.setDate(new Date(selectedTimePoint.date), false); 
        } else if (selectedDate) {
            // If a custom date was selected (not from a predefined timePoint)
             datePickerRef.current._flatpickrInstance.setDate(selectedDate, false);
        } else if (!timeMachineActive) { 
            // If time machine is deactivated, clear the calendar
            datePickerRef.current._flatpickrInstance.clear();
        }
    }
  }, [selectedTimePoint, selectedDate, timeMachineActive, datePickerRef]);


  if (!timeMachineData) return <p>Loading time machine data...</p>;

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="mb-4">
        <div className="flex flex-wrap items-center justify-between gap-3 p-2 bg-gray-50 rounded">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-lg font-medium text-gray-900 mr-2">
              <span role="img" aria-label="time machine">⏰</span> Bitcoin Time Machine
            </h3>
            <div className="flex items-center">
              <div className="text-sm font-medium text-gray-700 mr-2">Date:</div>
              <div className="relative">
                <input
                  ref={datePickerRef} // Ref is attached here
                  type="text"
                  placeholder="Select a date (since 2017)" // Updated placeholder
                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                />
              </div>
            </div>
          </div>
          <button
            onClick={() => setHistoricalTableOpen(!historicalTableOpen)}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm font-medium text-gray-700"
          >
            {historicalTableOpen ? 'Hide Historical Events' : 'Show Historical Events'}
          </button>
          {timeMachineActive && (
            <span className={`text-xs font-medium px-2.5 py-0.5 rounded bg-purple-100 text-purple-800 ml-auto`}>
              {selectedTimePoint && selectedTimePoint.name ? // Check if name exists to differentiate predefined from custom
                `Viewing: ${selectedTimePoint.name} (${new Date(selectedTimePoint.date).toLocaleDateString()})` :
                selectedDate ? `Viewing: Custom Date (${new Date(selectedDate).toLocaleDateString()})` :
                'Time Machine Active'
              }
            </span>
          )}
        </div>

        {!timeMachineActive && compositeMetrics && compositeMetrics.cos ? ( // Check compositeMetrics.cos as well
          <div className="bg-blue-50 p-2 rounded text-sm flex flex-wrap items-center justify-between">
            <div className="font-medium text-blue-800">Current Metrics:</div>
            <div className="flex space-x-4">
              <div>
                <span className="text-gray-600">
                  COS Monthly/Weekly:
                  <span className="ml-1 text-gray-400 cursor-help" title="Composite Overbought Score - Combines all indicators with weighted importance. Values above 75 suggest extreme overbought conditions.">ⓘ</span>
                </span>
                <span className={compositeMetrics.cos.monthly > 75 || compositeMetrics.cos.weekly > 75 ? 'ml-1 font-medium text-red-600' : 'ml-1 font-medium text-blue-600'}>
                  {compositeMetrics.cos.monthly.toFixed(1)} / {compositeMetrics.cos.weekly.toFixed(1)}
                </span>
                {compositeMetrics.cos.monthly > 90 || compositeMetrics.cos.weekly > 90 ?
                  <span className="ml-1 text-red-500">⚠️</span> :
                  null}
              </div>
              <div>
                <span className="text-gray-600">
                  BSI Monthly/Weekly:
                  <span className="ml-1 text-gray-400 cursor-help" title="Bull Strength Index - Measures the strength of the bullish trend. Values above 75% indicate a strong bullish trend, 50-75% a moderate trend, and below 50% a weak or bearish trend.">ⓘ</span>
                </span>
                <span className={compositeMetrics.bsi.monthly > 50 || compositeMetrics.bsi.weekly > 50 ? 'ml-1 font-medium text-red-600' : 'ml-1 font-medium text-blue-600'}>
                  {compositeMetrics.bsi.monthly.toFixed(0)}% / {compositeMetrics.bsi.weekly.toFixed(0)}%
                </span>
                {compositeMetrics.bsi.monthly > 75 || compositeMetrics.bsi.weekly > 75 ?
                  <span className="ml-1 text-red-500">⚠️</span> :
                  null}
              </div>
            </div>
            <div className="text-xs text-gray-500">
              Compare current metrics with historical events below
            </div>
          </div>
        ) : null}
      </div>

      {historicalTableOpen ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  COS (M/W)
                  <span className="ml-1 text-gray-400 cursor-help" title="Composite Overbought Score - Combines all indicators with weighted importance. Values above 75 suggest extreme overbought conditions.">ⓘ</span>
                </th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  BSI (M/W)
                  <span className="ml-1 text-gray-400 cursor-help" title="Bull Strength Index - Measures the strength of the bullish trend. Values above 75% indicate a strong bullish trend, 50-75% a moderate trend, and below 50% a weak or bearish trend.">ⓘ</span>
                </th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">1M Later</th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">6M Later</th>
                <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {timeMachineData.map(timePoint => (
                <tr key={timePoint.id} className={selectedTimePoint && selectedTimePoint.id === timePoint.id ? 'bg-purple-50' : ''}>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{new Date(timePoint.date).toLocaleDateString()}</td>
                  <td className="px-3 py-2 text-sm font-medium text-gray-900">
                    {timePoint.name}
                    <div className="text-xs text-gray-500 break-normal">{timePoint.description}</div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">${timePoint.price ? timePoint.price.toLocaleString() : 'N/A'}</td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    <span className={timePoint.compositeMetrics.cos.monthly > 75 ? 'text-red-600 font-medium' : 'text-gray-900'}>
                      {timePoint.compositeMetrics.cos.monthly.toFixed(1)}
                    </span>
                    {' / '}
                    <span className={timePoint.compositeMetrics.cos.weekly > 75 ? 'text-red-600 font-medium' : 'text-gray-900'}>
                      {timePoint.compositeMetrics.cos.weekly.toFixed(1)}
                    </span>
                    {timePoint.compositeMetrics.cos.monthly > 90 || timePoint.compositeMetrics.cos.weekly > 90 ?
                      <span className="ml-1 text-red-500">⚠️</span> :
                      null}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    <span className={timePoint.compositeMetrics.bsi.monthly > 50 ? 'text-red-600 font-medium' : 'text-gray-900'}>
                      {timePoint.compositeMetrics.bsi.monthly.toFixed(0)}%
                    </span>
                    {' / '}
                    <span className={timePoint.compositeMetrics.bsi.weekly > 50 ? 'text-red-600 font-medium' : 'text-gray-900'}>
                      {timePoint.compositeMetrics.bsi.weekly.toFixed(0)}%
                    </span>
                    {timePoint.compositeMetrics.bsi.monthly > 75 || timePoint.compositeMetrics.bsi.weekly > 75 ?
                      <span className="ml-1 text-red-500">⚠️</span> :
                      null}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    {timePoint.outcomes && timePoint.outcomes['1M'] && timePoint.outcomes['1M'].direction !== 'unknown' ? (
                      <span className={timePoint.outcomes['1M'].direction === 'up' ? 'text-green-600' : 'text-red-600'}>
                        {timePoint.outcomes['1M'].direction === 'up' ? '↑' : '↓'} {timePoint.outcomes['1M'].percentage}%
                      </span>
                    ) : (
                      <span className="text-gray-500 italic">N/A</span>
                    )}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    {timePoint.outcomes && timePoint.outcomes['6M'] && timePoint.outcomes['6M'].direction !== 'unknown' ? (
                      <span className={timePoint.outcomes['6M'].direction === 'up' ? 'text-green-600' : 'text-red-600'}>
                        {timePoint.outcomes['6M'].direction === 'up' ? '↑' : '↓'} {timePoint.outcomes['6M'].percentage}%
                      </span>
                    ) : (
                      <span className="text-gray-500 italic">N/A</span>
                    )}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-sm">
                    <button
                      onClick={() => onActivateTimeMachine(timePoint)}
                      className="text-purple-600 hover:text-purple-900"
                    >
                      {selectedTimePoint && selectedTimePoint.id === timePoint.id ? 'Viewing' : 'View Indicators'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-4 text-sm text-gray-500 bg-gray-50 rounded">
          Click "Show Historical Events" to view significant Bitcoin market events.
        </div>
      )}

      {selectedTimePoint && (
        <div className="mt-4 p-3 bg-gray-50 rounded text-sm">
          <p className="font-medium mb-2">{selectedTimePoint.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
            <div className="p-2 bg-white rounded shadow-sm">
              <div className="font-medium mb-1">Price at Event</div>
              <div className="text-lg">${selectedTimePoint.price ? selectedTimePoint.price.toLocaleString() : (selectedTimePoint.price === 0 ? '0.00' : 'Unknown')}</div>
            </div>
            
            <div className="p-2 bg-blue-50 rounded shadow-sm">
                <div className="font-medium mb-1">COS Monthly/Weekly</div>
                <div className="text-lg text-blue-600">
                {selectedTimePoint.compositeMetrics.cos.monthly.toFixed(1)} / {selectedTimePoint.compositeMetrics.cos.weekly.toFixed(1)}
                </div>
                <div className="text-xs text-gray-500">
                {selectedTimePoint.compositeMetrics.cos.monthly > 75 || selectedTimePoint.compositeMetrics.cos.weekly > 75 ?
                    'Extreme overbought' : 'Normal range'}
                </div>
            </div>

            <div className="p-2 bg-blue-50 rounded shadow-sm">
                <div className="font-medium mb-1">BSI Monthly/Weekly</div>
                <div className="text-lg text-blue-600">
                {selectedTimePoint.compositeMetrics.bsi.monthly.toFixed(0)}% / {selectedTimePoint.compositeMetrics.bsi.weekly.toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">
                {selectedTimePoint.compositeMetrics.bsi.monthly > 75 || selectedTimePoint.compositeMetrics.bsi.weekly > 75 ?
                    'Strong bullish trend' :
                    selectedTimePoint.compositeMetrics.bsi.monthly > 50 || selectedTimePoint.compositeMetrics.bsi.weekly > 50 ?
                    'Moderate bullish trend' : 'Weak or bearish trend'}
                </div>
            </div>
            {/* Iterate over outcomes safely */}
            {['1M', '6M', '12M'].map(period => {
                const outcome = selectedTimePoint.outcomes ? selectedTimePoint.outcomes[period] : null;
                const bgColor = outcome ? (outcome.direction === 'up' ? 'bg-green-50' : outcome.direction === 'down' ? 'bg-red-50' : 'bg-gray-50') : 'bg-gray-50';
                const textColor = outcome ? (outcome.direction === 'up' ? 'text-green-600' : outcome.direction === 'down' ? 'text-red-600' : 'text-gray-500') : 'text-gray-500';
                
                return (
                    <div key={period} className={`p-2 rounded shadow-sm ${bgColor}`}>
                        <div className="font-medium mb-1">{period} Later</div>
                        {outcome && outcome.direction && outcome.direction !== 'unknown' ? (
                        <div>
                            <div className="text-lg">
                                <span className={textColor}>
                                    {outcome.direction === 'up' ? '↑' : '↓'} {outcome.percentage}%
                                </span>
                            </div>
                            <div>${outcome.price ? outcome.price.toLocaleString() : (outcome.price === 0 ? '0.00': 'N/A')}</div>
                        </div>
                        ) : (
                        <div className="text-gray-500 italic">{outcome && outcome.price === 0 && outcome.direction === 'unknown' ? 'Future / Not Occurred' : 'N/A'}</div>
                        )}
                    </div>
                );
            })}
          </div>
        </div>
      )}
    </div>
  );
}