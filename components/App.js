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
  const [currentDataDetails, setCurrentDataDetails] = useState(null);

  const datePickerRef = useRef(null); // Ref for Flatpickr input element

  const fetchTimeMachineDataInternal = async () => {
    console.log('[fetchTimeMachineDataInternal] Starting...');
    const backendUrl = window.getBackendUrl('api/historical_time_points');
    console.log(`[fetchTimeMachineDataInternal] Fetching historical time points from: ${backendUrl}`);
    try {
      const response = await axios.get(backendUrl);
      console.log('[fetchTimeMachineDataInternal] Response from axios.get:', response);
      // Backend already processes historical_data.json to ensure BSI and calculate compositeMetrics
      const data = response.data.timePoints.map(point => ({
          ...point,
          // Ensure compositeMetrics are provided from backend's processing
          compositeMetrics: point.compositeMetrics
      }));
      console.log('[fetchTimeMachineDataInternal] Processed data:', data);
      setTimeMachineData(data);
      console.log('[fetchTimeMachineDataInternal] Time machine data loaded successfully from backend and processed.');
      return data;
    } catch (err) {
      console.error('[fetchTimeMachineDataInternal] Error loading time machine data from backend:', err);
      // Fallback data structure (simplified for brevity, ensure it matches your actual fallback needs)
      const fallbackData = [
        { id: 1, date: "2021-04-14", name: "Fallback Peak 1", price: 64895.00, description: "Fallback data", outcomes: {"1M":{}, "6M":{}, "12M":{}}, indicators: {rsi:{monthly:80,weekly:80}}, compositeMetrics: {cos:{monthly:0,weekly:0}, bsi:{monthly:0,weekly:0}}},
        { id: 2, date: "2021-11-10", name: "Fallback Peak 2", price: 69000.00, description: "Fallback data", outcomes: {"1M":{}, "6M":{}, "12M":{}}, indicators: {rsi:{monthly:85,weekly:85}}, compositeMetrics: {cos:{monthly:0,weekly:0}, bsi:{monthly:0,weekly:0}}},
      ]; // Fallback data now includes predefined compositeMetrics
      setTimeMachineData(fallbackData);
      console.log('[fetchTimeMachineDataInternal] Using fallback historical data.');
      return fallbackData;
    }
  };

  const activateTimeMachine = (timePoint) => {
    console.log('[activateTimeMachine] Starting...');
    if (!timePoint) {
      console.log('[activateTimeMachine] No timePoint provided, returning.');
      return;
    }
    console.log('[activateTimeMachine] Activating timePoint:', timePoint);

    const indicatorsToSet = timePoint.indicators || {};
    const compositeMetricsToSet = timePoint.compositeMetrics;
    const lastUpdateToSet = new Date(timePoint.date);
    const dataSourceToSet = 'timeMachine';

    console.log('[activateTimeMachine] Setting indicators:', indicatorsToSet);
    setIndicators(indicatorsToSet);
    console.log('[activateTimeMachine] Setting compositeMetrics:', compositeMetricsToSet);
    setCompositeMetrics(compositeMetricsToSet);
    console.log('[activateTimeMachine] Setting lastUpdate:', lastUpdateToSet);
    setLastUpdate(lastUpdateToSet);
    console.log('[activateTimeMachine] Setting dataSource:', dataSourceToSet);
    setDataSource(dataSourceToSet);
    setCurrentDataDetails(null); // Clear current data details when TM is active
    
    setSelectedTimePoint(timePoint);
    setTimeMachineActive(true);
    setSelectedDate(new Date(timePoint.date)); // For calendar consistency
    setError(null); 
    setLoading(false); 
    console.log(`[activateTimeMachine] Time machine activated: ${timePoint.name} (${timePoint.date})`);
  };

  const fetchData = async (attempt = 0) => {
    console.log('[fetchData] Starting...');
    setLoading(true);
    setError(null);
    const maxAttempts = 1; 
    let caughtApiError = null;

    try {
      const backendUrl = window.getBackendUrl('api/indicators');
      console.log(`[fetchData] Fetching data from: ${backendUrl}`);
      const response = await axios.get(backendUrl);
      console.log('[fetchData] Response from axios.get:', response);
      const data = response.data;

      setIndicators(data.indicators);
      setCompositeMetrics(data.compositeMetrics);
      setLastUpdate(data.lastUpdate ? new Date(data.lastUpdate) : new Date());
      setDataSource('kraken');
      setCurrentDataDetails({
        price: data.price,
        name: data.name,
        description: data.description,
        outcomes: data.outcomes,
        lastUpdate: data.lastUpdate
      });
      if(data.error_message) { 
        setError(data.error_message); 
      }
      console.log('[fetchData] Successfully fetched data from API');
    } catch (apiError) { 
      caughtApiError = apiError; 
      console.error('[fetchData] API Error in fetchData:', apiError);
      if (attempt < maxAttempts) {
          console.log(`[fetchData] Retrying fetchData, attempt ${attempt + 1}`);
          setTimeout(() => fetchData(attempt + 1), 3000); 
          return; 
      }

      console.log('[fetchData] Backend unavailable or max retries reached. Attempting to use latest historical data...');
      let historicalData = timeMachineData; 
      if (!historicalData || historicalData.length === 0) {
        console.log('[fetchData] Fetching historical data as fallback...');
        historicalData = await fetchTimeMachineDataInternal(); // Fetch if not already loaded
      }

      if (historicalData && historicalData.length > 0) {
        const sortedPoints = [...historicalData].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        const latestPoint = sortedPoints[0];
        console.log(`[fetchData] Using latest historical point as fallback: ${latestPoint.name} (${latestPoint.date})`);
        activateTimeMachine(latestPoint); 
        setError('Backend server unavailable. Displaying the most recent historical data point.');
      } else {
        console.log('[fetchData] No historical data available. Falling back to mock data...');
        const mockInd = { rsi: { monthly: 68, weekly: 72 }, stochRsi: { monthly: 75, weekly: 82 }, mfi: { monthly: 65, weekly: 78 }, crsi: { monthly: 82, weekly: 88 }, williamsR: { monthly: -25, weekly: -18 }, rvi: { monthly: 0.65, weekly: 0.72 }, adaptiveRsi: { monthly: 70, weekly: 75 }};
        setIndicators(mockInd);
        setCompositeMetrics({ cos: { monthly: 0, weekly: 0 }, bsi: { monthly: 0, weekly: 0 } });
        setLastUpdate(new Date());
        setDataSource('mock');
        setCurrentDataDetails({
            price: 'N/A',
            name: 'Mock Data Active',
            description: 'Displaying mock data due to backend unavailability.',
            outcomes: {}, 
            lastUpdate: new Date().toISOString()
        });
        setError('Backend server and historical data unavailable. Displaying mock data.');
        console.log('[fetchData] Fell back to mock data.');
      }
    } finally {
      if (!(caughtApiError && attempt < maxAttempts)) { 
        setLoading(false);
      }
    }
  };

  const refreshData = async () => {
    console.log('[refreshData] Starting...');
    if (timeMachineActive) {
      console.log('[refreshData] Time Machine active, deactivating first.');
      deactivateTimeMachine(); 
      return; 
    }
    console.log('[refreshData] Refresh button clicked. Calling fetchData().');
    try {
      const backendUrl = window.getBackendUrl('api/refresh');
      axios.post(backendUrl)
           .then(() => console.log('[refreshData] Conceptual /api/refresh POST successful'))
           .catch(err => console.warn('[refreshData] Conceptual /api/refresh POST failed:', err.message));
    } catch (e) {
      console.warn('[refreshData] Error trying to POST to /api/refresh:', e.message);
    }
    await fetchData(); 
  };

  const deactivateTimeMachine = async () => {
    console.log('[deactivateTimeMachine] Starting...');
    setSelectedTimePoint(null);
    setTimeMachineActive(false);
    setSelectedDate(null); 
    if (datePickerRef.current && datePickerRef.current._flatpickrInstance) {
      datePickerRef.current._flatpickrInstance.clear();
    }
    await fetchData(); 
    console.log('[deactivateTimeMachine] Time machine deactivated');
  };
  
  const fetchDataForDate = async (date) => {
    console.log('[fetchDataForDate] Starting with date:', date);
    if (!date) {
      console.log('[fetchDataForDate] No date provided, returning.');
      return;
    }
    setLoading(true);
    setError(null);
    setSelectedDate(date); 
    setCurrentDataDetails(null); // Clear current data details when fetching for a specific date

    try {
      const dateString = date.toISOString();
      const backendUrl = window.getBackendUrl(`api/indicators?date=${dateString}`);
      console.log(`[fetchDataForDate] Fetching data for date ${dateString} from: ${backendUrl}`);
      const response = await axios.get(backendUrl);
      console.log('[fetchDataForDate] Response from axios.get:', response);
      const data = response.data;

      if (data.error && !data.price && !data.indicators) { 
          const errorMsg = data.error || `No data could be retrieved for ${date.toLocaleDateString()}`;
          setError(errorMsg);
          setIndicators(null); 
          setCompositeMetrics(null); 
          const errorPoint = {
              date: dateString,
              name: `Error for ${date.toLocaleDateString()}`,
              description: errorMsg,
              price: null, indicators: {}, compositeMetrics: { cos: { monthly: 0, weekly: 0 }, bsi: { monthly: 0, weekly: 0 } }, outcomes: {}, isCustomDate: true
          };
          console.log('[fetchDataForDate] Creating errorPoint:', errorPoint);
          activateTimeMachine(errorPoint); 
      } else {
        const customPoint = {
            date: data.lastUpdate || dateString, 
            name: data.name || `Custom Date: ${date.toLocaleDateString()}`,
            price: data.price,
            description: data.description || "Custom date selected by user - data from Backend API",
            indicators: data.indicators || {}, 
            compositeMetrics: data.compositeMetrics,
            outcomes: data.outcomes || {}, 
            isCustomDate: true
        };
        console.log('[fetchDataForDate] Creating customPoint:', customPoint);
        activateTimeMachine(customPoint); 
        if(data.error_message) { 
            setError(data.error_message);
        }
      }
      console.log(`[fetchDataForDate] Successfully processed data request for date: ${dateString}`);
    } catch (apiErrorCatch) { 
      console.error('[fetchDataForDate] Hard API Error in fetchDataForDate:', apiErrorCatch);
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
          price: null, indicators: {}, compositeMetrics: { cos: { monthly: 0, weekly: 0 }, bsi: { monthly: 0, weekly: 0 } }, outcomes: {}, isCustomDate: true
      };
      console.log('[fetchDataForDate] Creating errorPoint from catch block:', errorPoint);
      activateTimeMachine(errorPoint); 
    } finally {
      if (!timeMachineActive && !loading) { 
          setLoading(false);
      } else if (timeMachineActive && loading) { 
          setLoading(false);
      }
    }
  };
  
  useEffect(() => {
    let isMounted = true;
    const loadInitialData = async () => {
      console.log('[useEffect] loadInitialData called.');
      if (isMounted) setLoading(true); 
      
      console.log('[useEffect] Calling fetchTimeMachineDataInternal...');
      await fetchTimeMachineDataInternal(); 
      
      if (isMounted && !timeMachineActive) { 
        console.log('[useEffect] Calling fetchData...');
        await fetchData(); 
      } else if (isMounted && timeMachineActive) {
        console.log('[useEffect] Time machine is active, not calling fetchData. Ensuring loading is false.');
        if (isMounted) setLoading(false);
      }
    };

    loadInitialData();

    const interval = setInterval(() => {
      if (isMounted && !timeMachineActive) {
        console.log("[useEffect] Interval: Fetching data");
        fetchData(); 
      }
    }, 5 * 60 * 1000); 

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

      {!timeMachineActive && currentDataDetails && <CurrentDataSummary details={currentDataDetails} />}

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