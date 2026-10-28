/**
 * WebPulse CompareSelector React Component
 * Replaces vanilla JS inline onchange handlers in version comparison
 * Provides interactive dropdowns and quick base/target swap feature
 */

const { useState, useCallback, useRef } = React;

function CompareSelector({ actionUrl, versions = [], initialV1, initialV2 }) {
  const [v1, setV1] = useState(String(initialV1));
  const [v2, setV2] = useState(String(initialV2));
  const formRef = useRef(null);

  const handleV1Change = useCallback((e) => {
    const val = e.target.value;
    setV1(val);
    if (formRef.current) {
      setTimeout(() => formRef.current.submit(), 10);
    }
  }, []);

  const handleV2Change = useCallback((e) => {
    const val = e.target.value;
    setV2(val);
    if (formRef.current) {
      setTimeout(() => formRef.current.submit(), 10);
    }
  }, []);

  const handleSwap = useCallback((e) => {
    e.preventDefault();
    const temp = v1;
    setV1(v2);
    setV2(temp);
    // Submit form with swapped values
    const form = formRef.current;
    if (form) {
      form.elements['v1'].value = v2;
      form.elements['v2'].value = temp;
      form.submit();
    }
  }, [v1, v2]);

  return (
    <form ref={formRef} method="GET" action={actionUrl} className="d-flex align-items-center gap-2">
      <div className="input-group input-group-sm">
        <span className="input-group-text bg-dark border-secondary text-dim small">Base</span>
        <select
          name="v1"
          value={v1}
          onChange={handleV1Change}
          className="form-select form-select-sm"
          style={{ minWidth: '160px' }}
        >
          {versions.map(v => (
            <option key={v.id} value={v.id}>
              {v.label} (#{v.number})
            </option>
          ))}
        </select>
      </div>

      <button
        type="button"
        onClick={handleSwap}
        className="btn btn-sm btn-outline-cyan px-2"
        title="Swap Base and Target releases"
      >
        <i className="bi bi-arrow-left-right"></i>
      </button>

      <div className="input-group input-group-sm">
        <span className="input-group-text bg-dark border-secondary text-dim small">Target</span>
        <select
          name="v2"
          value={v2}
          onChange={handleV2Change}
          className="form-select form-select-sm"
          style={{ minWidth: '160px' }}
        >
          {versions.map(v => (
            <option key={v.id} value={v.id}>
              {v.label} (#{v.number})
            </option>
          ))}
        </select>
      </div>
    </form>
  );
}

// Resilient mount logic
function mountCompareSelector() {
  const container = document.getElementById('react-compare-selector');
  if (container && !container.dataset.reactMounted) {
    container.dataset.reactMounted = 'true';
    try {
      const versionsData = JSON.parse(container.dataset.versions || '[]');
      const root = ReactDOM.createRoot(container);
      root.render(
        <CompareSelector
          actionUrl={container.dataset.actionUrl}
          versions={versionsData}
          initialV1={container.dataset.v1}
          initialV2={container.dataset.v2}
        />
      );
    } catch (err) {
      console.error('Failed to parse compare selector versions JSON:', err);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountCompareSelector);
} else {
  mountCompareSelector();
}

