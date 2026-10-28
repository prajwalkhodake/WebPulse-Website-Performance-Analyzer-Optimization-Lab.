/**
 * WebPulse FileInventoryFilter React Component
 * Replaces the vanilla JS filterFilesTable() function
 * Provides real-time search filtering for the file inventory table
 */

const { useState, useCallback, useEffect } = React;

function FileInventoryFilter() {
  const [query, setQuery] = useState('');

  const handleChange = useCallback((e) => {
    const value = e.target.value;
    setQuery(value);

    // Filter table rows in real time
    const rows = document.querySelectorAll('#fileInventoryTable .file-row');
    const lowerQuery = value.toLowerCase();
    rows.forEach(row => {
      const text = row.innerText.toLowerCase();
      row.style.display = text.includes(lowerQuery) ? '' : 'none';
    });
  }, []);

  return (
    <input
      type="text"
      className="form-control form-control-sm"
      placeholder="Filter files by path..."
      style={{ maxWidth: '260px' }}
      value={query}
      onChange={handleChange}
      id="fileSearchInput"
    />
  );
}

// Resilient mount logic
function mountFileInventoryFilter() {
  const container = document.getElementById('react-file-filter');
  if (container && !container.dataset.reactMounted) {
    container.dataset.reactMounted = 'true';
    const root = ReactDOM.createRoot(container);
    root.render(<FileInventoryFilter />);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountFileInventoryFilter);
} else {
  mountFileInventoryFilter();
}

