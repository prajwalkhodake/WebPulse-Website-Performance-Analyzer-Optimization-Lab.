/**
 * WebPulse CytoscapeGraph React Component
 * Renders the interactive dependency network graph with zoom/pan controls,
 * real-time node search filter, and interactive node inspector details panel.
 */

const { useState, useEffect, useRef, useCallback } = React;

function CytoscapeGraph({ graphDataUrl }) {
  const [cy, setCy] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEmpty, setIsEmpty] = useState(false);
  const containerRef = useRef(null);

  // Initialize Cytoscape
  useEffect(() => {
    if (!graphDataUrl || !containerRef.current) return;

    let cyInstance = null;
    let isCancelled = false;

    const initGraph = (cyLib, data) => {
      if (isCancelled || !containerRef.current) return;

      const nodes = (data && data.elements && data.elements.nodes) || [];
      const edges = (data && data.elements && data.elements.edges) || [];

      if (nodes.length === 0) {
        setIsEmpty(true);
        setLoading(false);
        return;
      }

      try {
        cyInstance = cyLib({
          container: containerRef.current,
          elements: { nodes, edges },
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
                'border-color': 'rgba(255,255,255,0.25)',
                'transition-property': 'background-color, border-color, width, height, opacity',
                'transition-duration': '0.2s'
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
              style: {
                'border-width': 4,
                'border-color': '#f8fafc',
                'width': 44,
                'height': 44
              }
            },
            {
              selector: 'edge',
              style: {
                'width': 2,
                'line-color': 'rgba(255,255,255,0.18)',
                'target-arrow-color': 'rgba(255,255,255,0.3)',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'arrow-scale': 1.1
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
              style: {
                'border-color': '#38bdf8',
                'border-width': 4,
                'underlay-color': '#38bdf8',
                'underlay-padding': 5,
                'underlay-opacity': 0.4
              }
            }
          ],
          layout: {
            name: 'cose',
            idealEdgeLength: 85,
            nodeOverlap: 25,
            refresh: 20,
            fit: true,
            padding: 35,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 450000,
            edgeElasticity: 100,
            animate: false
          }
        });

        // Event listener: select node
        cyInstance.on('tap', 'node', function(evt) {
          const nodeData = evt.target.data();
          setSelectedNode(nodeData);
        });

        // Event listener: click background to clear selection
        cyInstance.on('tap', function(evt) {
          if (evt.target === cyInstance) {
            setSelectedNode(null);
          }
        });

        setCy(cyInstance);
        setLoading(false);
      } catch (err) {
        console.error('Failed to initialize Cytoscape:', err);
        setError('Error rendering graph visualization: ' + err.message);
        setLoading(false);
      }
    };

    // Helper: wait for cytoscape script to be ready
    const resolveCy = (data) => {
      if (typeof cytoscape !== 'undefined') {
        initGraph(cytoscape, data);
      } else {
        let retries = 25;
        const interval = setInterval(() => {
          retries -= 1;
          if (typeof cytoscape !== 'undefined') {
            clearInterval(interval);
            initGraph(cytoscape, data);
          } else if (retries <= 0) {
            clearInterval(interval);
            setError('Cytoscape.js library failed to load.');
            setLoading(false);
          }
        }, 100);
      }
    };

    fetch(graphDataUrl)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        resolveCy(data);
      })
      .catch(err => {
        console.error('Failed to load graph data:', err);
        setError('Failed to fetch dependency graph data: ' + err.message);
        setLoading(false);
      });

    return () => {
      isCancelled = true;
      if (cyInstance) {
        try { cyInstance.destroy(); } catch (e) {}
      }
    };
  }, [graphDataUrl]);

  // Real-time search nodes effect
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
        n.style('opacity', (label.includes(q) || path.includes(q)) ? 1 : 0.15);
      });
    });
  }, [searchQuery, cy]);

  const handleFit = useCallback(() => {
    if (cy) cy.fit(null, 35);
  }, [cy]);

  const handleZoomIn = useCallback(() => {
    if (cy) cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  }, [cy]);

  const handleZoomOut = useCallback(() => {
    if (cy) cy.zoom({ level: cy.zoom() * 0.75, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  }, [cy]);

  const handleReLayout = useCallback(() => {
    if (cy) {
      const layout = cy.layout({ name: 'cose', fit: true, padding: 35, animate: true, animationDuration: 400 });
      layout.run();
    }
  }, [cy]);

  const getNodeRole = (nodeData) => {
    if (nodeData.is_entry) return '⭐ Project Entry Point';
    if (nodeData.file_type === 'broken_missing') return '❌ Missing / Broken Reference';
    return 'Asset Node';
  };

  return (
    <div className="row g-3">
      <div className="col-lg-9">
        <div className="card-wp p-3" style={{ position: 'relative' }}>
          {/* Viewport Container with Isolated Canvas DOM */}
          <div style={{ position: 'relative', height: '640px', width: '100%', background: '#080d1a', borderRadius: '8px', overflow: 'hidden' }}>
            <div
              ref={containerRef}
              id="cy-container"
              style={{ height: '100%', width: '100%', position: 'absolute', top: 0, left: 0 }}
            />

            {loading && (
              <div className="position-absolute top-50 start-50 translate-middle text-center text-muted" style={{ zIndex: 10 }}>
                <div className="spinner-border text-cyan mb-3" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <div className="small font-mono text-dim">Rendering dependency network...</div>
              </div>
            )}

            {error && (
              <div className="position-absolute top-50 start-50 translate-middle text-center text-rose p-3" style={{ zIndex: 10 }}>
                <i className="bi bi-exclamation-triangle-fill fs-2 d-block mb-2"></i>
                <div className="fw-semibold">{error}</div>
              </div>
            )}

            {!loading && !error && isEmpty && (
              <div className="position-absolute top-50 start-50 translate-middle text-center text-muted p-3" style={{ zIndex: 10 }}>
                <i className="bi bi-diagram-2 fs-2 d-block mb-2 text-dim"></i>
                <h6 className="fw-bold text-main mb-1">No Dependency Elements Found</h6>
                <p className="small text-muted mb-0">Run static analysis to parse files and extract links.</p>
              </div>
            )}
          </div>

          {/* Graph Controls Overlay */}
          <div
            className="d-flex align-items-center gap-2 position-absolute top-0 end-0 m-4 p-2 rounded-3 shadow"
            style={{
              background: 'rgba(15, 23, 42, 0.9)',
              backdropFilter: 'blur(8px)',
              border: '1px solid var(--wp-border)',
              zIndex: 20
            }}
          >
            <div className="input-group input-group-sm" style={{ width: '160px' }}>
              <span className="input-group-text bg-dark border-secondary text-dim p-1 px-2">
                <i className="bi bi-search"></i>
              </span>
              <input
                type="text"
                className="form-control"
                placeholder="Find node..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="btn btn-sm btn-outline-secondary" onClick={() => setSearchQuery('')}>
                  <i className="bi bi-x"></i>
                </button>
              )}
            </div>
            <button className="btn btn-dark btn-sm border-secondary text-dim" onClick={handleZoomIn} title="Zoom In">
              <i className="bi bi-plus-lg"></i>
            </button>
            <button className="btn btn-dark btn-sm border-secondary text-dim" onClick={handleZoomOut} title="Zoom Out">
              <i className="bi bi-dash-lg"></i>
            </button>
            <button className="btn btn-dark btn-sm border-secondary text-dim" onClick={handleFit} title="Fit to View">
              <i className="bi bi-arrows-fullscreen"></i>
            </button>
            <button className="btn btn-dark btn-sm border-secondary text-dim" onClick={handleReLayout} title="Rearrange Layout">
              <i className="bi bi-arrow-repeat"></i>
            </button>
          </div>
        </div>
      </div>

      {/* Node Inspector Details Panel */}
      <div className="col-lg-3">
        <div className="card-wp p-3 mb-3">
          <h6 className="fw-bold text-main mb-2">
            <i className="bi bi-info-circle text-cyan me-1"></i> Selected Node
          </h6>

          {!selectedNode ? (
            <div className="text-muted small py-4 text-center">
              <i className="bi bi-hand-index-thumb d-block fs-3 mb-2 text-dim"></i>
              Click any node in the graph to inspect asset details and dependencies.
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

// Resilient mount logic that runs whether DOMContentLoaded has fired or not
function mountCytoscapeComponent() {
  const container = document.getElementById('react-cytoscape-graph');
  if (container && !container.dataset.reactMounted) {
    container.dataset.reactMounted = 'true';
    const graphDataUrl = container.dataset.graphUrl;
    const root = ReactDOM.createRoot(container);
    root.render(<CytoscapeGraph graphDataUrl={graphDataUrl} />);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountCytoscapeComponent);
} else {
  mountCytoscapeComponent();
}
