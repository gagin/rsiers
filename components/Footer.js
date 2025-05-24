// ./components/Footer.js
function Footer({ dataSource, lastUpdate, timeMachineActive, selectedTimePoint, selectedDate, onDeactivateTimeMachine, error }) {
  const isBackendUnavailable = dataSource === 'mock' || (dataSource === 'timeMachine' && error && error.includes('Backend server unavailable'));
  return (
    <footer className="mt-12 text-center text-sm">
      <div className="mb-2">
        {dataSource === 'timeMachine' ? (
          <p className="text-purple-600">
            <span className="bg-purple-100 text-purple-800 text-xs font-medium px-2.5 py-0.5 rounded">Time Machine Active</span>
            <span className="ml-2">Viewing historical data from {lastUpdate ? new Date(lastUpdate).toLocaleDateString() : 'unknown date'}</span>
            <span className="ml-2 bg-purple-100 text-purple-800 text-xs font-medium px-2.5 py-0.5 rounded">
              {selectedTimePoint && selectedTimePoint.id ? 'Historical Data from JSON (via Backend)' :
               selectedTimePoint && selectedTimePoint.isCustomDate ? 'Historical Data from Backend (Kraken API)' :
               'Historical Data'}
            </span>
          </p>
        ) : dataSource === 'kraken' ? (
          <p className="text-gray-600">
            Data refreshes automatically every 5 minutes. Last refresh: {lastUpdate ? new Date(lastUpdate).toLocaleString() : 'Loading...'}
            <span className="ml-2 bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">Live Kraken Data (via Backend)</span>
          </p>
        ) : dataSource === 'mock' ? (
          <p className="text-amber-600">
            <span className="bg-amber-100 text-amber-800 text-xs font-medium px-2.5 py-0.5 rounded">Mock Data</span>
            <span className="ml-2">Using simulated data (backend or historical data unavailable)</span>
          </p>
        ) : (
          <p className="text-gray-600">Loading data source...</p>
        )}
      </div>
      <p className="mt-2 text-gray-600">
        <a href="https://docs.kraken.com/rest/" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
          Kraken API Documentation
        </a>
        {' | '}
        <a href="https://www.investopedia.com/terms/r/rsi.asp" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
          Learn about RSI
        </a>
        <span className={timeMachineActive && !isBackendUnavailable ? '' : 'hidden'}>
          {' | '}
          <button onClick={onDeactivateTimeMachine} className="text-purple-600 hover:underline">
            Exit Time Machine
          </button>
        </span>
        <span className="ml-2 text-gray-400">v0.3.0</span>
      </p>
      <p className={`mt-2 text-xs text-gray-500 ${timeMachineActive ? '' : 'hidden'}`}>
        Time Machine allows you to view indicator values at any historical date.
        Use the calendar control to select a specific date or click on a historical event in the table.
        <span className={selectedTimePoint && selectedTimePoint.id ? '' : 'hidden'}>
          Currently viewing historical event: {selectedTimePoint ? selectedTimePoint.name : ''} with pre-calculated data from JSON (served by backend).
        </span>
        <span className={selectedTimePoint && selectedTimePoint.isCustomDate ? '' : 'hidden'}>
          Currently viewing custom date: {selectedDate ? new Date(selectedDate).toLocaleDateString() : ''} with data fetched from Kraken API (via backend).
        </span>
        <br />
        <span className="font-medium mt-1 inline-block">Data Sources:</span> Historical events use pre-calculated data from `historical_data.json` (served by backend).
        Custom dates are fetched and calculated on the backend using Kraken API.
      </p>
    </footer>
  );
}