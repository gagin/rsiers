// ./components/CurrentDataSummary.js
function CurrentDataSummary({ details }) {
  if (!details) {
    return null;
  }

  // Format date for display
  const displayDate = details.lastUpdate ? new Date(details.lastUpdate).toLocaleString() : 'N/A';

  return (
    <div className="bg-white p-4 rounded-lg shadow mb-6">
      <h2 className="text-xl font-semibold mb-2">{details.name || 'Current Data'}</h2>
      {details.price && <p className="text-lg"><strong>Price:</strong> ${typeof details.price === 'number' ? details.price.toFixed(2) : details.price}</p>}
      <p className="text-sm text-gray-600">{details.description || ''}</p>
      <p className="text-sm text-gray-500 mt-1">Last updated: {displayDate}</p>
      {/* Optionally display outcomes summary here */}
      {/* Example for outcomes (customize as needed): */}
      {details.outcomes && Object.keys(details.outcomes).length > 0 && (
        <div className="mt-2">
          <h3 className="text-md font-semibold">Price Outcomes:</h3>
          <ul className="list-disc list-inside text-sm">
            {Object.entries(details.outcomes).map(([period, outcome]) => (
              <li key={period}>
                {period}: {outcome.direction || 'N/A'} ({outcome.percentage !== null && outcome.percentage !== undefined ? outcome.percentage.toFixed(2) : 'N/A'}%)
                {outcome.price !== null && outcome.price !== undefined ? ` (Target: $${outcome.price.toFixed(2)})` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
