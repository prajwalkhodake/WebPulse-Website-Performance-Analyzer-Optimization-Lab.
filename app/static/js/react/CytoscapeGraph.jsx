/**
 * WebPulse CytoscapeGraph React Component
 * Replaces the vanilla JS Cytoscape initialization, node search,
 * zoom controls, and node inspector panel
 */

const { useState, useEffect, useRef, useCallback } = React;

function CytoscapeGraph({ graphDataUrl }) {
  const [cy, setCy] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);

  // Initialize Cytoscape
  useEffect(() => {
    if (!graphDataUrl || !containerRef.current) return;

    fetch(graphDataUrl)
      .then(res => res.json())
      .then(data => {
        const cyInstance = cytoscape({
          container: containerRef.current,
          elements: data.elements,
          style: [
            {
              selector: 'node',
              style: {
                'label': 'data(label)',
                'color': '#f8fafc',
                'font-size': '11px',
                'font-family': 'Inter, sans-serif',
                'background-color': '#94a3b8',
                'text-valign': 'bottom',
                'text-margin-y': 5,
                'width': 34,
                'height': 34,
                'border-width': 2,
                'border-color': 'rgba(255,255,255,0.2)'
              }
            },
            {
              selector: 'node[file_type = "html"]',
              style: { 'background-color': '#38bdf8', 'border-color': '#7dd3fc' }
            },
            {
              selector: 'node[file_type = "css"]',
              style: { 'background-color': '#818cf8', 'border-color': '#a5b4fc' }
            },
            {
              selector: 'node[file_type = "javascript"]',
              style: { 'background-color': '#f59e0b', 'border-color': '#fcd34d' }
            },
            {
              selector: 'node[file_type = "image"]',
              style: { 'background-color': '#10b981', 'border-color': '#6ee7b7' }
            },
            {
              selector: 'node[file_type = "broken_missing"]',
              style: {
                'background-color': '#ef4444',
                'border-color': '#fca5a5',
                'shape': 'diamond',
                'width': 40,
                'height': 40
              }
            },
            {
              selector: 'node[?is_entry]',
              style: { 'border-width': 4, 'border-color': '#f8fafc', 'width': 44, 'height': 44 }
            },
            {
              selector: 'edge',
              style: {
                'width': 2,
                'line-color': 'rgba(255,255,255,0.15)',
                'target-arrow-color': 'rgba(255,255,255,0.25)',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier'
              }
            },
            {
              selector: 'edge[?is_broken]',
              style: {
                'line-color': '#ef4444',
                'target-arrow-color': '#ef4444',
                'line-style': 'dashed',
                'width': 3
              }
            },
            {
              selector: 'node:selected',
              style: { 'border-color': '#38bdf8', 'border-width': 4 }
            }
          ],
          layout: {
            name: 'cose',
            idealEdgeLength: 80,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 400000,
            edgeElasticity: 100
          }
        });

        cyInstance.on('tap', 'node', function(evt) {
          const nodeData = evt.target.data();
          setSelectedNode(nodeData);
        });

        setCy(cyInstance);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load graph data.');
        setLoading(false);
      });

    return () => {
      if (cy) cy.destroy();
    };
  }, [graphDataUrl]);

  // Search nodes effect
  useEffect(() => {
    if (!cy) return;
    const q = searchQuery.toLowerCase().trim();
    cy.batch(() => {
      if (!q) {
        cy.nodes().style('opacity', 1);
        return;
      }
      cy.nodes().forEach(n => {
        const label = (n.data('label') || '').toLowerCase();
        const path = (n.data('full_path') || '').toLowerCase();
        n.style('opacity', (label.includes(q) || path.includes(q)) ? 1 : 0.2);
      });
    });
  }, [searchQuery, cy]);

  const handleFit = useCallback(() => { if (cy) cy.fit(); }, [cy]);
  const handleZoomIn = useCallback(() => { if (cy) cy.zoom(cy.zoom() * 1.25); }, [cy]);
  const handleZoomOut = useCallback(() => { if (cy) cy.zoom(cy.zoom() * 0.8); }, [cy]);

  const getNodeRole = (nodeData) => {
    if (nodeData.is_entry) return '⭐ Project Entry Point';
    if (nodeData.file_type === 'broken_missing') return '❌ Missing Resource 404';
    return 'Passive Asset';
  };

  return (
    <div className="row g-3">
      <div className="col-lg-9">
        <div className="card-wp p-3" style={{ position: 'relative' }}>
          {/* Cytoscape viewport */}
          <div
            ref={containerRef}
            id="cy-container"
            style={{ height: '640px', width: '100%', borderRadius: '8px' }}
          >
            {loading && (
              <div className="p-5 text-center text-muted">
                <div className="spinner-border text-cyan mb-3" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <div>Loading dependency graph...</div>
              </div>
            )}
            {error && (
              <div className="p-5 text-center text-muted">{error}</div>
            )}
          </div>

          {/* Graph Controls Overlay */}
          <div
            className="d-flex align-items-center gap-2 position-absolute top-0 end-0 m-4 p-2 rounded-3 shadow"
            style={{
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(8px)',
              border: '1px solid var(--wp-border)'
            }}
          >
            <input
              type="text"
              className="form-control form-control-sm"
              placeholder="Find file..."
              style={{ width: '140px' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button className="btn btn-dark btn-sm border-secondary text-dim" onClick={handleZoomIn}>
              <i className="bi bi-plus-lg"></i>
            </button>
            <button className="btn btn-dark btn-sm border-secondary text-dim" onClick={handleZoomOut}>
              <i className="bi bi-dash-lg"></i>
            </button>
          </div>
        </div>
      </div>

      {/* Node Inspector Details */}
      <div className="col-lg-3">
        <div className="card-wp p-3 mb-3">
          <h6 className="fw-bold text-main mb-2">
            <i className="bi bi-info-circle text-cyan me-1"></i> Selected Node
          </h6>

          {!selectedNode ? (
            <div className="text-muted small py-3 text-center">
              Click any file node in the graph to inspect incoming/outgoing references and asset details.
            </div>
          ) : (
            <div>
              <div className="small text-dim text-uppercase fw-bold">File Path:</div>
              <div className="font-mono small text-main text-break mb-2">{selectedNode.full_path}</div>

              <div className="small text-dim text-uppercase fw-bold">Category:</div>
              <div className="mb-2">
                <span className="badge badge-info">{(selectedNode.file_type || '').toUpperCase()}</span>
              </div>

              <div className="small text-dim text-uppercase fw-bold">Size:</div>
              <div className="font-mono small text-main mb-3">{selectedNode.size_kb} KB</div>

              <div className="border-top pt-2" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
                <span className="small text-muted">{getNodeRole(selectedNode)}</span>
              </div>
            </div>
          )}
        </div>

        <div className="card-wp p-3">
          <h6 className="fw-bold text-main mb-3">
            <i className="bi bi-palette text-indigo me-1"></i> Legend
          </h6>
          <div className="d-flex flex-column gap-2 small">
            <div className="d-flex align-items-center gap-2">
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#38bdf8' }}></span>
              <span>HTML Document</span>
            </div>
            <div className="d-flex align-items-center gap-2">
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#818cf8' }}></span>
              <span>CSS Stylesheet</span>
            </div>
            <div className="d-flex align-items-center gap-2">
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#f59e0b' }}></span>
              <span>JavaScript Script</span>
            </div>
            <div className="d-flex align-items-center gap-2">
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#10b981' }}></span>
              <span>Image Asset</span>
            </div>
            <div className="d-flex align-items-center gap-2">
              <span style={{ width: '12px', height: '12px', borderRadius: '3px', background: '#ef4444' }}></span>
              <span>Broken / Missing Local Link</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Global function for Fit View button outside React tree
window.cyFitFromReact = null;

// Mount on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('react-cytoscape-graph');
  if (container) {
    const graphDataUrl = container.dataset.graphUrl;
    const root = ReactDOM.createRoot(container);
    root.render(<CytoscapeGraph graphDataUrl={graphDataUrl} />);
  }
});
