// ./components/ErrorDisplay.js
function ErrorDisplay({ error }) {
  if (!error) return null;
  return (
    <div className={`bg-red-100 text-red-800 p-4 rounded mb-6`}>
      {error}
    </div>
  );
}