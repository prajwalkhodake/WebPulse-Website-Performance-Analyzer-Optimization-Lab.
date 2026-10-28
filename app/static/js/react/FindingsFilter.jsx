/**
 * WebPulse FindingsFilter React Component
 * Replaces vanilla JS onchange="this.form.submit()" for filter dropdowns
 * Provides React-controlled select elements that auto-submit the form
 */

const { useState, useCallback, useRef } = React;

function FindingsFilterBar({ actionUrl, categoryFilter, severityFilter, searchQuery }) {
  const formRef = useRef(null);

  const handleAutoSubmit = useCallback(() => {
    if (formRef.current) formRef.current.submit();
  }, []);

  return (
    <form ref={formRef} method="GET" action={actionUrl} className="row g-2 align-items-center">
      <div className="col-md-5">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-dark border-secondary text-dim">
            <i className="bi bi-search"></i>
          </span>
          <input
            type="text"
            name="q"
            defaultValue={searchQuery}
            className="form-control"
            placeholder="Search by title, explanation, or filename..."
          />
        </div>
      </div>
      <div className="col-md-3">
        <select
          name="category"
          className="form-select form-select-sm"
          defaultValue={categoryFilter}
          onChange={handleAutoSubmit}
        >
          <option value="">All Categories</option>
          <option value="performance">Performance</option>
          <option value="accessibility">Accessibility</option>
          <option value="best_practices">Best Practices</option>
          <option value="seo">SEO &amp; Discoverability</option>
        </select>
      </div>
      <div className="col-md-3">
        <select
          name="severity"
          className="form-select form-select-sm"
          defaultValue={severityFilter}
          onChange={handleAutoSubmit}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Informational</option>
        </select>
      </div>
      <div className="col-md-1 text-end">
        <a href={actionUrl} className="btn btn-sm btn-outline-light w-100" title="Reset Filters">
          <i className="bi bi-x-circle"></i>
        </a>
      </div>
    </form>
  );
}

// Mount on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('react-findings-filter');
  if (container) {
    const root = ReactDOM.createRoot(container);
    root.render(
      <FindingsFilterBar
        actionUrl={container.dataset.actionUrl}
        categoryFilter={container.dataset.categoryFilter || ''}
        severityFilter={container.dataset.severityFilter || ''}
        searchQuery={container.dataset.searchQuery || ''}
      />
    );
  }
});
