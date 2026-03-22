// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});

// Property image gallery
function initializeGallery() {
    const mainImage = document.querySelector('#main-property-image');
    const thumbnails = document.querySelectorAll('.property-thumbnail');
    
    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                mainImage.src = this.src;
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
}

// Rating input handler
function handleRatingInput() {
    const ratingInput = document.querySelector('#id_rating');
    const ratingDisplay = document.querySelector('#rating-display');
    
    if (ratingInput && ratingDisplay) {
        ratingInput.addEventListener('input', function() {
            ratingDisplay.textContent = this.value;
        });
    }
}

// Map initialization for property location
function initializePropertyMap(lat, lng) {
    if (typeof L !== 'undefined' && document.getElementById('property-map')) {
        const map = L.map('property-map').setView([lat, lng], 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        L.marker([lat, lng]).addTo(map);
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Payment method selection
function handlePaymentMethodSelection() {
    const paymentMethods = document.querySelectorAll('.payment-method-option');
    if (paymentMethods.length > 0) {
        paymentMethods.forEach(method => {
            method.addEventListener('click', function() {
                paymentMethods.forEach(m => m.classList.remove('selected'));
                this.classList.add('selected');
                document.querySelector('#selected-payment-method').value = this.dataset.method;
            });
        });
    }
}

// Initialize all components
document.addEventListener('DOMContentLoaded', function() {
    initializeGallery();
    handleRatingInput();
    handlePaymentMethodSelection();
});