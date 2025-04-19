        document.getElementById('currentYear').textContent = new Date().getFullYear();

        // Mobile menu toggle
        const mobileMenuButton = document.getElementById('mobileMenuButton');
        const mobileMenu = document.getElementById('mobileMenu');

        // Hide mobile menu by default
        mobileMenu.style.display = 'none';

        mobileMenuButton.addEventListener('click', () => {
            if (mobileMenu.style.display === 'none') {
                mobileMenu.style.display = 'block';
            } else {
                mobileMenu.style.display = 'none';
            }
        });

// User dropdown menu functionality
const userMenuTrigger = document.getElementById('userMenuTrigger');
const userDropdown = document.getElementById('userDropdown');
const userMenuContainer = document.getElementById('userMenuContainer');

if (userMenuTrigger && userDropdown) {
    userMenuTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isExpanded = userMenuTrigger.getAttribute('aria-expanded') === 'true';
        userMenuTrigger.setAttribute('aria-expanded', !isExpanded);

        if (!isExpanded) {
            userDropdown.style.display = 'block';
            // Use setTimeout to trigger the transition
            setTimeout(() => {
                userDropdown.classList.add('show');
            }, 10);
        } else {
            userDropdown.classList.remove('show');
            // Wait for transition to complete before hiding
            setTimeout(() => {
                userDropdown.style.display = 'none';
            }, 200);
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (event) => {
        if (userMenuContainer && !userMenuContainer.contains(event.target)) {
            userDropdown.classList.remove('show');
            userMenuTrigger.setAttribute('aria-expanded', 'false');
            setTimeout(() => {
                userDropdown.style.display = 'none';
            }, 200);
        }
    });

    // Close dropdown when pressing Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && userDropdown.classList.contains('show')) {
            userDropdown.classList.remove('show');
            userMenuTrigger.setAttribute('aria-expanded', 'false');
            setTimeout(() => {
                userDropdown.style.display = 'none';
            }, 200);
        }
    });
}
        // Message dismissal
        const messageCloseButtons = document.querySelectorAll('.message-close');
        messageCloseButtons.forEach(button => {
            button.addEventListener('click', function() {
                const messageAlert = this.closest('.message-alert');
                messageAlert.remove();
            });
        });

        // Add fade-in animation to page content on load
        const pageContent = document.getElementById('page-content');
        document.addEventListener('DOMContentLoaded', function() {
            if (pageContent) {
                pageContent.classList.add('animate-fade-in');
            }

            // Add animation classes to elements with data-animate attribute
            const animatedElements = document.querySelectorAll('[data-animate]');
            animatedElements.forEach((element, index) => {
                const animationType = element.getAttribute('data-animate') || 'fade-in';
                const delay = element.getAttribute('data-delay') || (index * 100);
                element.classList.add(`animate-${animationType}`, `delay-${delay}`);
            });
        });

        // Tab functionality
        function setupTabs() {
            const tabButtons = document.querySelectorAll('.tab-button');
            const tabContents = document.querySelectorAll('.tab-content');

            if (tabButtons.length > 0) {
                tabButtons.forEach(button => {
                    button.addEventListener('click', function() {
                        const tabName = this.getAttribute('data-tab');

                        // Hide all tab contents
                        tabContents.forEach(content => {
                            content.classList.add('hidden');
                        });

                        // Show selected tab content
                        const selectedTab = document.getElementById(`${tabName}-tab`);
                        if (selectedTab) {
                            selectedTab.classList.remove('hidden');
                            // Add animation to the tab content
                            selectedTab.classList.add('animate-fade-in');
                        }

                        // Update active tab button
                        tabButtons.forEach(btn => {
                            btn.classList.remove('active');
                        });

                        this.classList.add('active');

                        // Store active tab in session storage
                        sessionStorage.setItem('activeTab', tabName);
                    });
                });

                // Restore active tab from session storage
                const activeTab = sessionStorage.getItem('activeTab');
                if (activeTab) {
                    const tabToActivate = document.querySelector(`.tab-button[data-tab="${activeTab}"]`);
                    if (tabToActivate) {
                        tabToActivate.click();
                    }
                }
            }
        }

        // Run tab setup on DOM content loaded
        document.addEventListener('DOMContentLoaded', setupTabs);