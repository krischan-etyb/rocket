/**
 * Rocket Logistic - Main JavaScript
 * Language switching, navigation, and interactions
 */

(function() {
    'use strict';

    var currentLang = 'en';

    // =============================================
    // Mobile Navigation
    // =============================================

    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    const navLinks = document.querySelectorAll('.nav__link');

    navToggle.addEventListener('click', function() {
        navToggle.classList.toggle('active');
        navMenu.classList.toggle('active');
        document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });

    // Close menu when clicking a link
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navMenu.classList.contains('active') &&
            !navMenu.contains(e.target) &&
            !navToggle.contains(e.target)) {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    });

    // =============================================
    // Smooth Scroll Navigation
    // =============================================

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            const target = document.querySelector(href);

            if (target) {
                const headerHeight = document.getElementById('header').offsetHeight;
                const targetPosition = target.offsetTop - headerHeight;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // =============================================
    // Sticky Header & Scroll to Top
    // =============================================

    const header = document.getElementById('header');
    const scrollTopBtn = document.getElementById('scroll-top');

    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;

        // Add shadow when scrolled
        if (currentScroll > 50) {
            header.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.15)';
        } else {
            header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }

        // Show/hide scroll-to-top button
        if (scrollTopBtn) {
            if (currentScroll > 300) {
                scrollTopBtn.classList.add('visible');
            } else {
                scrollTopBtn.classList.remove('visible');
            }
        }
    });

    if (scrollTopBtn) {
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // =============================================
    // Contact Form Validation & Submission
    // =============================================

    const contactForm = document.getElementById('contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form values
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const message = document.getElementById('message').value.trim();
            const loadDate = document.getElementById('load-date').value;
            const dateFlexibility = document.getElementById('date-flexibility').value;
            const gpsTracking = document.getElementById('gps-tracking').checked;

            // Simple validation
            let isValid = true;

            // Name validation
            if (name.length < 2) {
                showError('name', 'Please enter your name');
                isValid = false;
            } else {
                clearError('name');
            }

            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showError('email', 'Please enter a valid email');
                isValid = false;
            } else {
                clearError('email');
            }

            // Message validation
            if (message.length < 10) {
                showError('message', 'Please enter a message (min 10 characters)');
                isValid = false;
            } else {
                clearError('message');
            }

            if (isValid) {
                // Send data to Flask backend API
                const formData = {
                    name: name,
                    email: email,
                    phone: phone,
                    message: message,
                    load_date: loadDate,
                    date_flexibility: dateFlexibility,
                    gps_tracking: gpsTracking,
                    language: currentLang
                };

                // Disable submit button to prevent double submission
                const submitButton = contactForm.querySelector('button[type="submit"]');
                const originalButtonText = submitButton.textContent;
                submitButton.disabled = true;
                submitButton.textContent = 'Sending...';

                // API endpoint - update for production
                const apiUrl = '/api/contact';

                // Send POST request to backend
                fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showFormOverlay('success');
                        contactForm.reset();
                    } else {
                        const errorMessage = data.error || 'An error occurred. Please try again.';
                        showFormOverlay('error', errorMessage);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    const errorMessage = 'Network error. Please check your connection and try again.';
                    showFormOverlay('error', errorMessage);
                })
                .finally(() => {
                    submitButton.disabled = false;
                    submitButton.textContent = originalButtonText;
                });
            }
        });
    }

    function showError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const formGroup = field.closest('.form-group');

        const existingError = formGroup.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }

        field.classList.add('field-error');

        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.textContent = message;
        formGroup.appendChild(errorDiv);
    }

    function clearError(fieldId) {
        const field = document.getElementById(fieldId);
        const formGroup = field.closest('.form-group');

        field.classList.remove('field-error');

        const existingError = formGroup.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }
    }

    function showFormOverlay(type, customMessage) {
        const isSuccess = type === 'success';
        const title = isSuccess ? 'Message Sent!' : 'Error';
        const message = isSuccess
            ? 'Thank you! Your message has been sent. We will contact you shortly.'
            : customMessage;
        const iconClass = isSuccess ? 'form-overlay__icon--success' : 'form-overlay__icon--error';
        const iconPath = isSuccess
            ? 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'
            : 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z';

        const overlay = document.createElement('div');
        overlay.className = 'form-overlay';
        overlay.innerHTML = `
            <div class="form-overlay__content">
                <svg class="form-overlay__icon ${iconClass}" viewBox="0 0 24 24" fill="currentColor">
                    <path d="${iconPath}"/>
                </svg>
                <h3 class="form-overlay__title">${title}</h3>
                <p class="form-overlay__text">${message}</p>
                <button class="form-overlay__btn">OK</button>
            </div>
        `;

        document.body.appendChild(overlay);

        const closeOverlay = () => overlay.remove();
        overlay.querySelector('.form-overlay__btn').addEventListener('click', closeOverlay);
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) closeOverlay();
        });
    }

    // =============================================
    // Intersection Observer for Animations
    // =============================================

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!prefersReducedMotion) {
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe service cards and stats
        document.querySelectorAll('.service-card, .stat').forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = `opacity 0.5s ease ${index * 0.1}s, transform 0.5s ease ${index * 0.1}s`;
            observer.observe(el);
        });
    }

})();
