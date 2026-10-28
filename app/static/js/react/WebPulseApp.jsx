/**
 * WebPulse Core React Application
 * Replaces vanilla JavaScript with React components for:
 * - Flash alert auto-dismissal
 * - Bootstrap tooltip initialization
 * - Active navigation highlighting
 * - Form submission spinner feedback
 */

const { useState, useEffect, useRef, useCallback } = React;

/* ──────────────────────────────────────────────────────────
   FlashAlertManager
   Auto-dismisses Bootstrap .alert-dismissible after 5 sec
   ────────────────────────────────────────────────────────── */
function FlashAlertManager() {
  useEffect(() => {
    const alerts = document.querySelectorAll('.alert-dismissible');
    const timers = [];
    alerts.forEach(alert => {
      const timer = setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }, 5000);
      timers.push(timer);
    });
    return () => timers.forEach(clearTimeout);
  }, []);

  return null; // headless component
}

/* ──────────────────────────────────────────────────────────
   TooltipInitializer
   Finds and initializes all Bootstrap tooltips on mount
   ────────────────────────────────────────────────────────── */
function TooltipInitializer() {
  useEffect(() => {
    const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const instances = Array.from(tooltipEls).map(el => new bootstrap.Tooltip(el));
    return () => instances.forEach(t => t.dispose());
  }, []);

  return null;
}

/* ──────────────────────────────────────────────────────────
   ActiveNavHighlighter
   Marks sidebar and navbar links with .active on match
   ────────────────────────────────────────────────────────── */
function ActiveNavHighlighter() {
  useEffect(() => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav-item, .navbar-nav .nav-link');
    navLinks.forEach(link => {
      if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
      }
    });
  }, []);

  return null;
}

/* ──────────────────────────────────────────────────────────
   FormSubmitSpinner
   Adds spinner + disabled state on form[data-submit-loader] submit
   ────────────────────────────────────────────────────────── */
function FormSubmitSpinner() {
  useEffect(() => {
    const forms = document.querySelectorAll('form[data-submit-loader]');

    const handlers = [];
    forms.forEach(form => {
      const handler = (e) => {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
          submitBtn.dataset.originalText = submitBtn.innerHTML || submitBtn.value;
          submitBtn.disabled = true;
          if (submitBtn.tagName.toLowerCase() === 'input') {
            submitBtn.value = 'Processing...';
          } else {
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
          }
        }
      };
      form.addEventListener('submit', handler);
      handlers.push({ form, handler });
    });

    return () => handlers.forEach(({ form, handler }) => form.removeEventListener('submit', handler));
  }, []);

  return null;
}

/* ──────────────────────────────────────────────────────────
   WebPulseApp — Root React Component
   Orchestrates all headless micro-interaction components
   ────────────────────────────────────────────────────────── */
function WebPulseApp() {
  return (
    React.createElement(React.Fragment, null,
      React.createElement(FlashAlertManager, null),
      React.createElement(TooltipInitializer, null),
      React.createElement(ActiveNavHighlighter, null),
      React.createElement(FormSubmitSpinner, null)
    )
  );
}

/* ──────────────────────────────────────────────────────────
   Mount the React root
   ────────────────────────────────────────────────────────── */
function mountWebPulseApp() {
  const appRoot = document.getElementById('webpulse-react-root');
  if (appRoot && !appRoot.dataset.reactMounted) {
    appRoot.dataset.reactMounted = 'true';
    const root = ReactDOM.createRoot(appRoot);
    root.render(React.createElement(WebPulseApp, null));
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountWebPulseApp);
} else {
  mountWebPulseApp();
}

