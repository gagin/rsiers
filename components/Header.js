// ./components/Header.js
function Header({ dataSource, loading, timeMachineActive, onRefresh, error }) {
  const isBackendUnavailable = dataSource === 'mock' || (dataSource === 'timeMachine' && error && error.includes('Backend server unavailable'));

  return (
    <header className="mb-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Bitcoin Indicator Dashboard <span className="text-sm font-normal text-gray-500">v0.3.0</span></h1>
        {isBackendUnavailable ? (
          <button
            onClick={onRefresh} // Assuming onRefresh will try to fetch again
            className="flex items-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            disabled={loading}
          >
            <span className="mr-2 text-lg" role="img" aria-label="red light">🔴</span>
            {loading ? 'Retrying...' : 'Backend unavailable, retry'}
          </button>
        ) : (
          <button
            onClick={onRefresh}
            className={`px-4 py-2 ${timeMachineActive ? 'bg-amber-600' : 'bg-green-600'} text-white rounded`}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : timeMachineActive ? 'Exit Time Machine' : 'Refresh Data'}
          </button>
        )}
      </div>
    </header>
  );
}