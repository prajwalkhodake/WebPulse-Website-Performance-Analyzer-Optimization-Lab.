/**
 * WebPulse UploadDropzone React Component
 * Replaces vanilla JS drag-and-drop file upload interactions
 * Renders interactively on the upload page
 */

const { useState, useEffect, useRef, useCallback } = React;

function UploadDropzone() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = useCallback((files) => {
    if (files && files[0]) {
      setSelectedFile(files[0]);

      // Sync with the actual form file input
      const realInput = document.getElementById('archiveInput');
      if (realInput && files !== realInput.files) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(files[0]);
        realInput.files = dataTransfer.files;
      }
    }
  }, []);

  const handleClick = useCallback(() => {
    const realInput = document.getElementById('archiveInput');
    if (realInput) realInput.click();
  }, []);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  // Listen for changes on the hidden real input
  useEffect(() => {
    const realInput = document.getElementById('archiveInput');
    if (!realInput) return;

    const changeHandler = () => handleFileSelect(realInput.files);
    realInput.addEventListener('change', changeHandler);
    return () => realInput.removeEventListener('change', changeHandler);
  }, [handleFileSelect]);

  const sizeMb = selectedFile ? (selectedFile.size / (1024 * 1024)).toFixed(2) : null;

  const dropzoneStyle = {
    borderColor: selectedFile ? 'var(--wp-cyan)' : (isDragOver ? 'var(--wp-cyan)' : undefined),
    backgroundColor: selectedFile ? 'rgba(56, 189, 248, 0.08)' : (isDragOver ? 'rgba(56, 189, 248, 0.04)' : undefined),
    cursor: 'pointer'
  };

  return (
    <div
      className={`upload-dropzone mb-4 ${isDragOver ? 'dragover' : ''}`}
      style={dropzoneStyle}
      onClick={handleClick}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <i className={`bi ${selectedFile ? 'bi-check-circle-fill text-emerald' : 'bi-cloud-arrow-up text-cyan'} display-4 d-block mb-3`}></i>
      <h5 className="fw-bold text-main mb-1">
        {selectedFile ? selectedFile.name : 'Click to browse or drag and drop your project ZIP file'}
      </h5>
      <p className="text-muted small mb-0">
        {selectedFile ? `${sizeMb} MB — Ready to Ingest` : 'Accepts .zip archives only (up to 50 MB max)'}
      </p>
    </div>
  );
}

// Resilient mount logic
function mountUploadDropzone() {
  const container = document.getElementById('react-upload-dropzone');
  if (container && !container.dataset.reactMounted) {
    container.dataset.reactMounted = 'true';
    const root = ReactDOM.createRoot(container);
    root.render(<UploadDropzone />);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountUploadDropzone);
} else {
  mountUploadDropzone();
}

