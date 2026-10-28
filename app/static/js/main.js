/**
 * WebPulse Core Frontend Scripts
 * Provides micro-interactions, alert auto-dismissal, form validation styling, and tooltips.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss flash alerts after 5 seconds
    const flashAlerts = document.querySelectorAll('.alert-dismissible');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // 2. Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // 3. Highlight current sidebar navigation item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav-item, .navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // 4. Form submission spinner feedback
    const formsWithSubmit = document.querySelectorAll('form[data-submit-loader]');
    formsWithSubmit.forEach(form => {
        form.addEventListener('submit', (e) => {
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
        });
    });
});
