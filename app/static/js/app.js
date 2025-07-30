// Homepage JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize homepage
    initializeHomepage();
    
    // Check system status
    checkSystemStatus();
    
    // Setup animations
    setupAnimations();
});

function initializeHomepage() {
    console.log('🧠 0BullshitIntelligence - Homepage loaded');
    
    // Add smooth scroll behavior for any anchor links
    setupSmoothScroll();
    
    // Setup interactive elements
    setupInteractiveElements();
    
    // Setup welcome time
    setupWelcomeTime();
}

function setupSmoothScroll() {
    // Handle smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function setupInteractiveElements() {
    // Add hover effects to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(-4px)';
        });
    });
    
    // Add click effect to CTA buttons
    const ctaButtons = document.querySelectorAll('.cta-button, .secondary-button');
    ctaButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            createRippleEffect(this, e);
        });
    });
}

function createRippleEffect(element, event) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    `;
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    // Add ripple animation CSS if not exists
    if (!document.querySelector('#ripple-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-style';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function setupWelcomeTime() {
    const welcomeTimeElement = document.querySelector('#welcomeTime');
    if (welcomeTimeElement) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
        welcomeTimeElement.textContent = timeString;
    }
}

function setupAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.feature-card, .demo-preview, .footer-section');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

async function checkSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        updateSystemStatus(data.success ? 'healthy' : 'degraded');
        
        if (data.data && data.data.components) {
            console.log('System components status:', data.data.components);
        }
        
    } catch (error) {
        console.warn('Could not check system status:', error);
        updateSystemStatus('unknown');
    }
}

function updateSystemStatus(status) {
    const statusElements = document.querySelectorAll('.system-status');
    statusElements.forEach(element => {
        const indicator = element.querySelector('.status-indicator');
        const text = element.querySelector('span:not(.status-indicator)');
        
        if (indicator && text) {
            switch (status) {
                case 'healthy':
                    indicator.textContent = '🟢';
                    text.textContent = 'Todos los sistemas operativos';
                    break;
                case 'degraded':
                    indicator.textContent = '🟡';
                    text.textContent = 'Algunos servicios limitados';
                    break;
                case 'unknown':
                default:
                    indicator.textContent = '⚪';
                    text.textContent = 'Estado desconocido';
                    break;
            }
        }
    });
}

// Utility functions for smooth user experience
function showLoading() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loadingOverlay';
    loadingOverlay.innerHTML = `
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(15, 15, 35, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            backdrop-filter: blur(5px);
        ">
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
                color: white;
            ">
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 3px solid rgba(99, 102, 241, 0.3);
                    border-top: 3px solid #6366f1;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <p>Cargando...</p>
            </div>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

// Handle page navigation with loading states
document.addEventListener('click', function(e) {
    const link = e.target.closest('a[href="/chat"]');
    if (link) {
        e.preventDefault();
        showLoading();
        
        // Small delay to show loading state
        setTimeout(() => {
            window.location.href = '/chat';
        }, 300);
    }
});

// Add keyboard navigation support
document.addEventListener('keydown', function(e) {
    // Enter key on CTA buttons
    if (e.key === 'Enter') {
        const focusedElement = document.activeElement;
        if (focusedElement.classList.contains('cta-button') || 
            focusedElement.classList.contains('secondary-button')) {
            focusedElement.click();
        }
    }
});

// Progressive enhancement for better accessibility
function enhanceAccessibility() {
    // Add ARIA labels where needed
    const ctaButtons = document.querySelectorAll('.cta-button');
    ctaButtons.forEach(button => {
        if (!button.getAttribute('aria-label')) {
            button.setAttribute('aria-label', 'Comenzar nueva conversación con 0BullshitIntelligence');
        }
    });
    
    // Add focus indicators
    const interactiveElements = document.querySelectorAll('button, a, .feature-card');
    interactiveElements.forEach(element => {
        element.addEventListener('focus', function() {
            this.style.outline = '2px solid #6366f1';
            this.style.outlineOffset = '2px';
        });
        
        element.addEventListener('blur', function() {
            this.style.outline = 'none';
        });
    });
}

// Initialize accessibility enhancements
setTimeout(enhanceAccessibility, 100);

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                console.log(`🚀 Page load time: ${Math.round(perfData.loadEventEnd)}ms`);
            }
        }, 0);
    });
}