/**
 * WebPulse WaterfallViewer React Component
 * Replaces the static network waterfall table with an interactive, DevTools-grade
 * resource inspector with live filtering, searching, sorting, and hover metrics.
 */

const { useState, useMemo } = React;

function WaterfallViewer({ resources = [], maxDuration = 1000, browserInfo = '' }) {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('start_time'); // start_time, duration, size, name

  // Calculate unique types
  const types = useMemo(() => {
    const s = new Set();
    resources.forEach(r => {
      if (r.resource_type) s.add(r.resource_type.toLowerCase());
    });
    return Array.from(s);
  }, [resources]);

  // Filtered & sorted resources
  const filtered = useMemo(() => {
    return resources.filter(r => {
      // Type filter
      if (typeFilter === 'failed') {
        if (!r.is_failed && (!r.status_code || r.status_code < 400)) return false;
      } else if (typeFilter !== 'all') {
        if ((r.resource_type || '').toLowerCase() !== typeFilter) return false;
      }

      // Search filter
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchesName = (r.resource_name || '').toLowerCase().includes(q);
        const matchesUrl = (r.url || '').toLowerCase().includes(q);
        if (!matchesName && !matchesUrl) return false;
      }

      return true;
    }).sort((a, b) => {
      if (sortBy === 'duration') return b.duration_ms - a.duration_ms;
      if (sortBy === 'size') return b.transfer_size_kb - a.transfer_size_kb;
      if (sortBy === 'name') return (a.resource_name || '').localeCompare(b.resource_name || '');
      return (a.start_time_ms || 0) - (b.start_time_ms || 0);
    });
  }, [resources, search, typeFilter, sortBy]);

  const totalFilteredSize = useMemo(() => {
    return filtered.reduce((acc, r) => acc + (r.transfer_size_kb || 0), 0).toFixed(1);
  }, [filtered]);

  return (
    <div>
      {/* Controls & Filter Bar */}
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 border-bottom pb-3 mb-3" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
        <div className="d-flex flex-wrap align-items-center gap-2">
          {/* Search Box */}
          <div className="input-group input-group-sm" style={{ width: '220px' }}>
            <span className="input-group-text bg-dark border-secondary text-dim">
              <i className="bi bi-search"></i>
            </span>
            <input
              type="text"
              className="form-control"
              placeholder="Filter resources..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                onClick={() => setSearch('')}
              >
                <i className="bi bi-x"></i>
              </button>
            )}
          </div>

          {/* Type Filters */}
          <div className="btn-group btn-group-sm" role="group">
            <button
              type="button"
              className={`btn ${typeFilter === 'all' ? 'btn-cyan' : 'btn-outline-light'}`}
              onClick={() => setTypeFilter('all')}
            >
              All ({resources.length})
            </button>
            {types.map(t => (
              <button
                key={t}
                type="button"
                className={`btn ${typeFilter === t ? 'btn-cyan' : 'btn-outline-light'} text-capitalize`}
                onClick={() => setTypeFilter(t)}
              >
                {t}
              </button>
            ))}
            <button
              type="button"
              className={`btn ${typeFilter === 'failed' ? 'btn-rose' : 'btn-outline-light'}`}
              onClick={() => setTypeFilter('failed')}
            >
              Failed
            </button>
          </div>
        </div>

        {/* Sort & Count */}
        <div className="d-flex align-items-center gap-3">
          <div className="d-flex align-items-center gap-1 small text-dim">
            <span>Sort:</span>
            <select
              className="form-select form-select-sm"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ width: '130px' }}
            >
              <option value="start_time">Timeline</option>
              <option value="duration">Slowest First</option>
              <option value="size">Largest First</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>
          <span className="small text-dim font-mono">
            {filtered.length} of {resources.length} ({totalFilteredSize} KB)
          </span>
          {browserInfo && (
            <span className="badge badge-info font-mono d-none d-lg-inline-block">
              {browserInfo}
            </span>
          )}
        </div>
      </div>

      {/* Waterfall Table */}
      <div className="table-responsive">
        <table className="waterfall-table">
          <thead>
            <tr>
              <th style={{ width: '80px' }}>Status</th>
              <th style={{ width: '300px' }}>Resource Name</th>
              <th style={{ width: '100px' }}>Type</th>
              <th style={{ width: '90px' }}>Size</th>
              <th style={{ width: '90px' }}>Duration</th>
              <th>Timing Waterfall</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-4 text-dim">
                  <i className="bi bi-funnel fs-4 d-block mb-1"></i>
                  No resources match the selected filter.
                </td>
              </tr>
            ) : (
              filtered.map((r, idx) => {
                const isFail = r.is_failed || (r.status_code && r.status_code >= 400);
                const max = maxDuration > 0 ? maxDuration : 1000;
                const leftPct = Math.min(Math.max(0, (r.start_time_ms / max) * 100), 90);
                const widthPct = Math.max(3, Math.min(100 - leftPct, (r.duration_ms / max) * 100));

                return (
                  <tr key={idx}>
                    <td>
                      <span className={`badge ${isFail ? 'badge-critical' : 'badge-success'} font-mono`}>
                        {r.status_code || (isFail ? 'FAIL' : 200)}
                      </span>
                    </td>
                    <td className="text-truncate" style={{ maxWidth: '300px' }} title={r.url}>
                      <code className="text-main small">{r.resource_name}</code>
                    </td>
                    <td>
                      <span className="badge bg-secondary font-mono small text-uppercase">
                        {r.resource_type || 'other'}
                      </span>
                    </td>
                    <td className="font-mono small text-dim">
                      {r.transfer_size_kb} KB
                    </td>
                    <td className="font-mono small text-dim">
                      {Number(r.duration_ms).toFixed(1)} ms
                    </td>
                    <td>
                      <div
                        className="waterfall-bar-container"
                        title={`Start: ${r.start_time_ms?.toFixed(1) || 0}ms | Duration: ${r.duration_ms?.toFixed(1) || 0}ms`}
                      >
                        <div
                          className={`waterfall-bar bar-${r.resource_type || 'other'}`}
                          style={{
                            left: `${leftPct}%`,
                            width: `${widthPct}%`,
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Mount on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('react-waterfall-viewer');
  if (container) {
    try {
      const resourcesData = JSON.parse(container.dataset.resources || '[]');
      const maxDuration = parseFloat(container.dataset.maxDuration || '1000');
      const browserInfo = container.dataset.browserInfo || '';
      const root = ReactDOM.createRoot(container);
      root.render(
        <WaterfallViewer
          resources={resourcesData}
          maxDuration={maxDuration}
          browserInfo={browserInfo}
        />
      );
    } catch (err) {
      console.error('Failed to parse WaterfallViewer resources JSON:', err);
    }
  }
});
