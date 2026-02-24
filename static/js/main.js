// Main JavaScript file

$(document).ready(function() {
    // Form validation
    $('#searchForm').on('submit', function(e) {
        const query = $('#query').val().trim();
        if (!query) {
            e.preventDefault();
            showToast('Please enter a product name', 'error');
            return false;
        }
        
        const platforms = $('input[name="platforms"]:checked').length;
        if (platforms === 0) {
            e.preventDefault();
            showToast('Please select at least one platform', 'error');
            return false;
        }
        
        // Show loading state
        $('#searchBtn').html('<span class="spinner-border spinner-border-sm"></span> Searching...').prop('disabled', true);
    });
    
    // Auto-dismiss alerts
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
});

// Toast notification function
function showToast(message, type = 'info') {
    const toastHTML = `
        <div class="toast-container">
            <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <strong class="me-auto">Notification</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        </div>
    `;
    
    $('body').append(toastHTML);
    setTimeout(function() {
        $('.toast-container').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 3000);
}

// Price formatter
function formatPrice(price, currency = '$') {
    if (!price || price === 'N/A') return 'N/A';
    const numericPrice = parseFloat(price.replace(/[^0-9.-]+/g, ''));
    if (isNaN(numericPrice)) return price;
    return currency + numericPrice.toFixed(2);
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }, function(err) {
        showToast('Failed to copy', 'error');
    });
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}