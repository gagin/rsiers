// ./components/App.js
const { useState, useEffect, useRef } = React;

// Global utility function (can be moved to a utils.js)
window.getBackendUrl = function(endpoint) {
  // Ensure this always returns the correct base URL for your backend
  // For local development, it's typically http://localhost:PORT
  return `http://localhost:5001/${endpoint}`;
};

function App() {
  const [indicators, setIndicators] = useState(null);
  const [compositeMetrics, setCompositeMetrics] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('loading'); // 'kraken', 'mock', 'timeMachine', 'loading'
  const [timeMachineData, setTimeMachineData] = useState(null); // Array of historical time points
  const [selectedTimePoint, setSelectedTimePoint] = useState(null); // The specific historical point being viewed
  const [timeMachineActive, setTimeMachineActive] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null); // Date selected in the calendar

  const datePickerRef = useRef(null); // Ref for Flatpickr input element

  // Calculate composite metrics - Fallback if backend doesn't provide them
  // This function is also used by fetchTimeMachineDataInternal to ensure historical points have metrics
  const calculateCompositeMetrics = (indicatorsData) => {
    if (!indicatorsData || Object.keys(indicatorsData).length === 0) {
        return { cos: { monthly: 0, weekly: 0 }, bsi: { monthly: 0, weekly: 0 } };
    }
    // Weights for Composite Overbought Score
    const weights = {stochRsi:0.30,crsi:0.20,mfi:0.20,rsi:0.15,williamsR:0.10,rvi:0.03,adaptiveRsi:0.02};
    // Overbought thresholds
    const thresholds = {rsi:70,stochRsi:80,mfi:70,crsi:90,williamsR:-20,rvi:0.7,adaptiveRsi:70};
    
    let monthlyCOS = 0, weeklyCOS = 0, monthlyBSI = 0, weeklyBSI = 0;

    Object.keys(indicatorsData).forEach(key => {
      if (!weights[key] || !thresholds[key] || !indicatorsData[key] || 
          typeof indicatorsData[key].monthly !== 'number' || typeof indicatorsData[key].weekly !== 'number') {
        // Skip if indicator data is missing, not a number, or not in weights/thresholds
        return;
      }
      
      const monthlyVal = indicatorsData[key].monthly;
      const weeklyVal = indicatorsData[key].weekly;
      const thresholdVal = thresholds[key];
      const weightVal = weights[key];

      // COS calculation: Normalize and weight
      // For Williams %R, lower values (e.g., -5) are more overbought than higher (e.g., -50)
      // So, if value <= threshold, it's 100% overbought contribution for Williams %R.
      // Otherwise, scale based on how far it is from 0 relative to threshold.
      let normM_cos = (key === 'williamsR') 
                      ? (monthlyVal <= thresholdVal ? 100 : (Math.abs(monthlyVal) / Math.abs(thresholdVal)) * 100) 
                      : (monthlyVal / thresholdVal) * 100;
      monthlyCOS += weightVal * Math.min(150, Math.max(-50, normM_cos)); // Cap normalized values
      
      let normW_cos = (key === 'williamsR') 
                      ? (weeklyVal <= thresholdVal ? 100 : (Math.abs(weeklyVal) / Math.abs(thresholdVal)) * 100) 
                      : (weeklyVal / thresholdVal) * 100;
      weeklyCOS += weightVal * Math.min(150, Math.max(-50, normW_cos));


      // BSI calculation: Measures distance from a neutral point towards overbought
      // Neutral for Williams %R is -50. For others, 50% of threshold.
      const neutralM = (key === 'williamsR' ? -50.0 : thresholdVal * 0.5);
      const neutralW = (key === 'williamsR' ? -50.0 : thresholdVal * 0.5);
      
      // Denominator: distance from neutral to threshold
      // For Williams %R, threshold (-20) is 'higher' (less negative) than neutral (-50)
      const denM = (key === 'williamsR' ? (neutralM - thresholdVal) : (thresholdVal - neutralM));
      const denW = (key === 'williamsR' ? (neutralW - thresholdVal) : (thresholdVal - neutralW));

      let distM = 0;
      if (Math.abs(denM) > 1e-6) { // Avoid division by zero
        // Numerator: distance from value to neutral
        // For Williams %R, movement from neutral (-50) towards threshold (-20) is bullish strength
        distM = (key === 'williamsR') ? (neutralM - monthlyVal) / denM * 100 : (monthlyVal - neutralM) / denM * 100;
      }
      monthlyBSI += Math.min(100, Math.max(0, distM)) * weightVal; // Scale to 0-100 and weight
      
      let distW = 0;
      if (Math.abs(denW) > 1e-6) {
        distW = (key === 'williamsR') ? (neutralW - weeklyVal) / denW * 100 : (weeklyVal - neutralW) / denW * 100;
      }
      weeklyBSI += Math.min(100, Math.max(0, distW)) * weightVal;
    });

    return {
      cos: { monthly: Math.min(100,Math.max(0,monthlyCOS)), weekly: Math.min(100,Math.max(0,weeklyCOS)) },
      bsi: { monthly: Math.min(100,Math.max(0,monthlyBSI)), weekly: Math.min(100,Math.max(0,weeklyBSI)) }
    };
  };

  const fetchTimeMachineDataInternal = async () => {
    const backendUrl = window.getBackendUrl('api/historical_time_points');
    console.log(`Fetching historical time points from: ${backendUrl}`);
    try {
      const response = await axios.get(backendUrl);
      // Backend already processes historical_data.json to ensure BSI and calculate compositeMetrics
      const data = response.data.timePoints.map(point => ({
          ...point,
          // Ensure compositeMetrics are calculated if missing from backend's processing (should not happen ideally)
          compositeMetrics: point.compositeMetrics || calculateCompositeMetrics(point.indicators)
      }));
      setTimeMachineData(data);
      console.log('Time machine data loaded successfully from backend and processed.');
      return data;
    } catch (err) {
      console.error('Failed to load time machine data from backend:', err);
      // Fallback data structure (simplified for brevity, ensure it matches your actual fallback needs)
      const fallbackData = [
        { id: 1, date: "2021-04-14", name: "Fallback Peak 1", price: 64895.00, description: "Fallback data", outcomes: {"1M":{}, "6M":{}, "12M":{}}, indicators: {rsi:{monthly:80,weekly:80}}, compositeMetrics: {cos:{monthly:80,weekly:80}, bsi:{monthly:80,weekly:80}}},
        { id: 2, date: "2021-11-10", name: "Fallback Peak 2", price: 69000.00, description: "Fallback data", outcomes: {"1M":{}, "6M":{}, "12M":{}}, indicators: {rsi:{monthly:85,weekly:85}}, compositeMetrics: {cos:{monthly:85,weekly:85}, bsi:{monthly:85,weekly:85}}},
      ].map(point => ({ ...point, compositeMetrics: calculateCompositeMetrics(point.indicators) })); // Ensure fallback also has metrics
      setTimeMachineData(fallbackData);
      console.log('Using fallback historical data.');
      return fallbackData;
    }
  };

  const activateTimeMachine = (timePoint) => {
    if (!timePoint) return;
    setSelectedTimePoint(timePoint);
    setTimeMachineActive(true);
    setSelectedDate(new Date(timePoint.date)); // For calendar consistency
    
    setIndicators(timePoint.indicators || {}); // Ensure indicators is an object
    // Ensure compositeMetrics are always calculated or taken from the point
    setCompositeMetrics(timePoint.compositeMetrics || calculateCompositeMetrics(timePoint.indicators));
    
    setLastUpdate(new Date(timePoint.date));
    setDataSource('timeMachine');
    setError(null); 
    setLoading(false); 
    console.log(`Time machine activated: ${timePoint.name} (${timePoint.date})`);
  };

  const fetchData = async (attempt = 0) => {
    setLoading(true);
    setError(null);
    const maxAttempts = 1; 
    let caughtApiError = null;

    try {
      const backendUrl = window.getBackendUrl('api/indicators');
      console.log(`Fetching data from: ${backendUrl}`);
      const response = await axios.get(backendUrl);
      const data = response.data;

      setIndicators(data.indicators);
      // Backend should always provide compositeMetrics. Fallback is here just in case.
      setCompositeMetrics(data.compositeMetrics || calculateCompositeMetrics(data.indicators));
      setLastUpdate(data.lastUpdate ? new Date(data.lastUpdate) : new Date());
      setDataSource('kraken');
      if(data.error_message) { 
        setError(data.error_message); // Display non-critical errors from backend (e.g. partial data)
      }
      console.log('Successfully fetched data from API');
    } catch (apiError) { 
      caughtApiError = apiError; 
      console.error('API Error in fetchData:', apiError);
      if (attempt < maxAttempts) {
          console.log(`Retrying fetchData, attempt ${attempt + 1}`);
          setTimeout(() => fetchData(attempt + 1), 3000); 
          return; 
      }

      console.log('Backend unavailable or max retries reached. Attempting to use latest historical data...');
      let historicalData = timeMachineData; 
      if (!historicalData || historicalData.length === 0) {
        historicalData = await fetchTimeMachineDataInternal(); // Fetch if not already loaded
      }

      if (historicalData && historicalData.length > 0) {
        const sortedPoints = [...historicalData].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        const latestPoint = sortedPoints[0];
        console.log(`Using latest historical point as fallback: ${latestPoint.name} (${latestPoint.date})`);
        activateTimeMachine(latestPoint); 
        setError('Backend server unavailable. Displaying the most recent historical data point.');
      } else {
        console.log('No historical data available. Falling back to mock data...');
        const mockInd = { rsi: { monthly: 68, weekly: 72 }, stochRsi: { monthly: 75, weekly: 82 }, mfi: { monthly: 65, weekly: 78 }, crsi: { monthly: 82, weekly: 88 }, williamsR: { monthly: -25, weekly: -18 }, rvi: { monthly: 0.65, weekly: 0.72 }, adaptiveRsi: { monthly: 70, weekly: 75 }};
        setIndicators(mockInd);
        setCompositeMetrics(calculateCompositeMetrics(mockInd));
        setLastUpdate(new Date());
        setDataSource('mock');
        setError('Backend server and historical data unavailable. Displaying mock data.');
      }
    } finally {
      if (!(caughtApiError && attempt < maxAttempts)) { 
        setLoading(false);
      }
    }
  };

  const refreshData = async () => {
    if (timeMachineActive) {
      deactivateTimeMachine(); 
      return; 
    }
    console.log('Refresh button clicked. Calling fetchData().');
    try {
      const backendUrl = window.getBackendUrl('api/refresh');
      axios.post(backendUrl).then(() => console.log('Conceptual /api/refresh POST successful'))
                           .catch(err => console.warn('Conceptual /api/refresh POST failed:', err.message));
    } catch (e) {
      console.warn('Error trying to POST to /api/refresh:', e.message);
    }
    await fetchData(); 
  };

  const deactivateTimeMachine = async () => {
    setSelectedTimePoint(null);
    setTimeMachineActive(false);
    setSelectedDate(null); 
    if (datePickerRef.current && datePickerRef.current._flatpickrInstance) {
      datePickerRef.current._flatpickrInstance.clear();
    }
    await fetchData(); 
    console.log('Time machine deactivated');
  };
  
  const fetchDataForDate = async (date) => {
    if (!date) return;
    setLoading(true);
    setError(null);
    setSelectedDate(date); // Keep selectedDate updated for calendar to show what was picked

    try {
      const dateString = date.toISOString();
      const backendUrl = window.getBackendUrl(`api/indicators?date=${dateString}`);
      console.log(`Fetching data for date ${dateString} from: ${backendUrl}`);
      const response = await axios.get(backendUrl);
      const data = response.data;

      // Check if the backend itself signaled an error but returned 200 (e.g. for partial data)
      // or if it's a successful data retrieval.
      if (data.error && !data.price && !data.indicators) { // A more definitive error scenario from backend
          setError(data.error || `No data could be retrieved for ${date.toLocaleDateString()}`);
          // Clear out data fields to reflect error state
          setIndicators(null); 
          setCompositeMetrics(null); 
          // Create a minimal time point to display the error context
          const errorPoint = {
              date: dateString,
              name: `Error for ${date.toLocaleDateString()}`,
              description: data.error || `Failed to fetch complete data for this date.`,
              price: null, indicators: {}, compositeMetrics: calculateCompositeMetrics(null), outcomes: {}, isCustomDate: true
          };
          activateTimeMachine(errorPoint); // Use activateTimeMachine to set TM state correctly with error info
      } else {
        // Successful fetch or partial data (where `data.error_message` might exist)
        const customPoint = {
            date: data.lastUpdate || dateString, 
            name: data.name || `Custom Date: ${date.toLocaleDateString()}`,
            price: data.price,
            description: data.description || "Custom date selected by user - data from Backend API",
            indicators: data.indicators || {}, // Ensure indicators is an object
            compositeMetrics: data.compositeMetrics || calculateCompositeMetrics(data.indicators),
            outcomes: data.outcomes || {}, // Ensure outcomes is an object
            isCustomDate: true
        };
        activateTimeMachine(customPoint); 
        if(data.error_message) { // Display non-critical errors (e.g. partial data warning)
            setError(data.error_message);
        }
      }
      console.log(`Successfully processed data request for date: ${dateString}`);
    } catch (apiErrorCatch) { // Catch for network errors or non-2xx responses from axios.get
      console.error('Hard API Error in fetchDataForDate:', apiErrorCatch);
      const errorMessage = (apiErrorCatch.response && apiErrorCatch.response.data && apiErrorCatch.response.data.error)
                           || apiErrorCatch.message
                           || `Failed to fetch data for ${date.toLocaleDateString()}.`;
      setError(errorMessage);
      setIndicators(null); 
      setCompositeMetrics(null);
      const errorPoint = {
          date: date.toISOString(),
          name: `Error for ${date.toLocaleDateString()}`,
          description: errorMessage,
          price: null, indicators: {}, compositeMetrics: calculateCompositeMetrics(null), outcomes: {}, isCustomDate: true
      };
      activateTimeMachine(errorPoint); // Use activateTimeMachine to manage TM state
    } finally {
      // setLoading(false) is handled by activateTimeMachine or if an error path doesn't call it.
      // To be safe, ensure it's always set if not transitioning through activateTimeMachine.
      if (!timeMachineActive && !loading) { // If TM didn't get activated (e.g. early error path)
          setLoading(false);
      } else if (timeMachineActive && loading) { // If TM is active but still loading (shouldn't happen often here)
          setLoading(false);
      }
    }
  };
  
  useEffect(() => {
    let isMounted = true;
    const loadInitialData = async () => {
      // Set loading true at the very start of initial data loading sequence
      if (isMounted) setLoading(true); 
      
      await fetchTimeMachineDataInternal(); // Load historical points first
      
      if (isMounted && !timeMachineActive) { 
        await fetchData(); // Then load current data if not already in TM
      } else if (isMounted && timeMachineActive) {
        // If somehow TM is active but no data, ensure loading is false
        if (isMounted) setLoading(false);
      }
    };

    loadInitialData();

    const interval = setInterval(() => {
      if (isMounted && !timeMachineActive) {
        console.log("Interval: Fetching data");
        fetchData(); // Regular refresh
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []); // Empty dependency array: runs once on mount.

  return (
    <div className="container mx-auto px-4 py-8">
      <Header
        dataSource={dataSource}
        loading={loading}
        timeMachineActive={timeMachineActive}
        onRefresh={refreshData}
        error={error}
      />
      <ErrorDisplay error={error} />
      
      <TimeMachine
        timeMachineData={timeMachineData}
        selectedTimePoint={selectedTimePoint}
        timeMachineActive={timeMachineActive}
        selectedDate={selectedDate}
        onActivateTimeMachine={activateTimeMachine} // Pass the function itself
        onFetchDataForDate={fetchDataForDate}     // Pass the function itself
        datePickerRef={datePickerRef}
        compositeMetrics={compositeMetrics} // For comparison display when TM not active
      />

      <div className="bg-white p-4 rounded-lg shadow mb-6 mt-6"> {/* Added mt-6 for spacing */}
        <p className="text-gray-700 mb-4">
          Technical analysis is a kind of astrology, where people draw lines and waves to see patterns in the sky.
          Yet, the principle of price following the mood of the market is surprisingly solid, and RSI works quite well,
          reliably correlating with peak events. RSI has problems like lag and lack of normalization,
          so we use a bucket of other RSI-like indicators to compensate for its shortcomings while maintaining the illusion of precision.
        </p>
      </div>

      {/* Show loading indicator if loading AND (no indicators yet OR there's no overriding error) */}
      {loading && (!indicators || (indicators && !error)) ? <LoadingIndicator /> : null}
      
      {/* Show indicator table if not loading OR (loading but indicators are already present from previous fetch)
          AND indicators data is valid */}
      {(!loading || (loading && indicators)) && indicators && Object.keys(indicators).length > 0 && (
        <IndicatorTable indicators={indicators} />
      )}
      
      {/* Show composite metrics similarly */}
      {(!loading || (loading && compositeMetrics)) && compositeMetrics && indicators && Object.keys(indicators).length > 0 && (
        <CompositeMetrics metrics={compositeMetrics} />
      )}
      
      <Footer
        dataSource={dataSource}
        lastUpdate={lastUpdate}
        timeMachineActive={timeMachineActive}
        selectedTimePoint={selectedTimePoint}
        selectedDate={selectedDate}
        onDeactivateTimeMachine={deactivateTimeMachine} // Pass the function
        error={error}
      />
    </div>
  );
}