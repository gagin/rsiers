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
  compositeMetrics, // Current composite metrics from App.js (live data)
  currentDataDetails // Details of the current, non-time-machine data from App.js
}) {
  const [historicalTableOpen, setHistoricalTableOpen] = useState(false);

  // Determine what to display: historical point or current data details
  const displayDetails = timeMachineActive && selectedTimePoint
    ? selectedTimePoint
    : (!timeMachineActive && currentDataDetails ? currentDataDetails : null);

  // const isDisplayingCurrentData = !timeMachineActive && currentDataDetails; // Can be used for specific conditional rendering if needed

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


  // if (!timeMachineData && !currentDataDetails) return <p>Loading time machine data or current details...</p>;
  // If TM is not active and there are no current details, it might mean initial load before first fetch.
  if (timeMachineActive && !timeMachineData) return <p>Loading time machine historical data...</p>;


  return (
    <div className="bg-white p-4 rounded-lg shadow">
      {/* Time Machine Controls - Only show if TM can be activated or is active */}
      {(timeMachineData || !timeMachineActive) && (
      <div className="mb-4">
        <div className="flex flex-wrap items-center justify-between gap-3 p-2 bg-gray-50 rounded">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-lg font-medium text-gray-900 mr-2">
              <span role="img" aria-label="time machine">⏰</span> Bitcoin Time Machine
            </h3>
            {/* Date picker is part of TM functionality, enable/show when TM is usable */}
            <div className="flex items-center">
              <div className="text-sm font-medium text-gray-700 mr-2">Date:</div>
              <div className="relative">
                <input
                  ref={datePickerRef}
                  type="text"
                  placeholder="Select a date (since 2017)"
                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                  disabled={!timeMachineData} // Disable if no historical data to pick against initially
                />
              </div>
            </div>
          </div>
          {timeMachineData && ( // Only show button if historical data is available
            <button
              onClick={() => setHistoricalTableOpen(!historicalTableOpen)}
              className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm font-medium text-gray-700"
            >
              {historicalTableOpen ? 'Hide Historical Events' : 'Show Historical Events'}
            </button>
          )}
          {timeMachineActive && (
            <span className={`text-xs font-medium px-2.5 py-0.5 rounded bg-purple-100 text-purple-800 ml-auto`}>
              {selectedTimePoint && selectedTimePoint.name ?
                `Viewing: ${selectedTimePoint.name} (${new Date(selectedTimePoint.date).toLocaleDateString()})` :
                selectedDate ? `Viewing: Custom Date (${new Date(selectedDate).toLocaleDateString()})` :
                'Time Machine Active'
              }
            </span>
          )}
        </div>
      </div>
      )}

      {/* Unified Display Area for Current or Historical Data */}
      {displayDetails && (
        <div className="bg-gray-100 p-4 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-2">{displayDetails.name || 'Data Details'}</h2>
          {displayDetails.price !== undefined && displayDetails.price !== null && (
            <p className="text-lg">
              <strong>Price:</strong>
              {typeof displayDetails.price === 'number' ? ` $${displayDetails.price.toFixed(2)}` : ` ${displayDetails.price}`}
            </p>
          )}
          <p className="text-sm text-gray-600">{displayDetails.description || ''}</p>
          <p className="text-sm text-gray-500 mt-1">
            Last updated: {new Date(displayDetails.date || displayDetails.lastUpdate).toLocaleString()}
          </p>

          {/* Outcomes Display */}
          {displayDetails.outcomes && Object.keys(displayDetails.outcomes).length > 0 && (
            <div className="mt-3">
              <h3 className="text-md font-semibold">Price Outcomes:</h3>
              <ul className="list-disc list-inside text-sm">
                {Object.entries(displayDetails.outcomes).map(([period, outcome]) => (
                  <li key={period}>
                    {period}: {outcome.direction || 'N/A'}
                    ({outcome.percentage !== null && outcome.percentage !== undefined ? outcome.percentage.toFixed(2) : 'N/A'}%)
                    {outcome.price !== null && outcome.price !== undefined ? ` (Target: $${outcome.price.toFixed(2)})` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Display Composite Metrics of the selectedTimePoint or currentDataDetails */}
          {displayDetails.compositeMetrics && displayDetails.compositeMetrics.cos && (
            <div className="mt-3">
              <h3 className="text-md font-semibold">Composite Metrics for this view:</h3>
               <div className="flex space-x-4 text-sm">
                <div>
                    <span className="text-gray-600">COS (M/W): </span>
                    <span className={displayDetails.compositeMetrics.cos.monthly > 75 || displayDetails.compositeMetrics.cos.weekly > 75 ? 'font-medium text-red-600' : 'font-medium text-blue-600'}>
                    {displayDetails.compositeMetrics.cos.monthly.toFixed(1)} / {displayDetails.compositeMetrics.cos.weekly.toFixed(1)}
                    </span>
                </div>
                <div>
                    <span className="text-gray-600">BSI (M/W): </span>
                    <span className={displayDetails.compositeMetrics.bsi.monthly > 50 || displayDetails.compositeMetrics.bsi.weekly > 50 ? 'font-medium text-red-600' : 'font-medium text-blue-600'}>
                    {displayDetails.compositeMetrics.bsi.monthly.toFixed(0)}% / {displayDetails.compositeMetrics.bsi.weekly.toFixed(0)}%
                    </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Comparison with Live/Current Composite Metrics - Only if TM is active and a historical point is selected */}
      {timeMachineActive && selectedTimePoint && compositeMetrics && compositeMetrics.cos && (
        <div className="bg-blue-50 p-2 rounded text-sm flex flex-wrap items-center justify-between mb-4">
          <div className="font-medium text-blue-800">Compare with Current Live Metrics:</div>
          <div className="flex space-x-4">
            <div>
              <span className="text-gray-600">
                COS M/W:
                <span className="ml-1 text-gray-400 cursor-help" title="Composite Overbought Score - Current live data.">ⓘ</span>
              </span>
              <span className={compositeMetrics.cos.monthly > 75 || compositeMetrics.cos.weekly > 75 ? 'ml-1 font-medium text-red-600' : 'ml-1 font-medium text-blue-600'}>
                {compositeMetrics.cos.monthly.toFixed(1)} / {compositeMetrics.cos.weekly.toFixed(1)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">
                BSI M/W:
                <span className="ml-1 text-gray-400 cursor-help" title="Bull Strength Index - Current live data.">ⓘ</span>
              </span>
              <span className={compositeMetrics.bsi.monthly > 50 || compositeMetrics.bsi.weekly > 50 ? 'ml-1 font-medium text-red-600' : 'ml-1 font-medium text-blue-600'}>
                {compositeMetrics.bsi.monthly.toFixed(0)}% / {compositeMetrics.bsi.weekly.toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Historical Events Table - only show if data exists and button is toggled */}
      {timeMachineData && historicalTableOpen && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            {/* ... table head ... */}
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
      )}
      {timeMachineData && !historicalTableOpen && !timeMachineActive && (
         <div className="text-center py-4 text-sm text-gray-500 bg-gray-50 rounded">
          Click "Show Historical Events" to explore past market conditions.
        </div>
      )}

      {/* Detailed view of selectedTimePoint's indicators and outcomes - only if TM is active */}
      {/* This section is removed as its content is now part of displayDetails block above */}
      {/* {selectedTimePoint && ( <div className="mt-4 p-3 bg-gray-50 rounded text-sm"> ... </div> )} */}
    </div>
  );
}