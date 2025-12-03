// Dark mode management
        function initTheme() {
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

            if (savedTheme) {
                document.documentElement.setAttribute('data-theme', savedTheme);
            } else if (prefersDark) {
                document.documentElement.setAttribute('data-theme', 'dark');
            }

            updateThemeIcon();
        }

        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon();
        }

        function updateThemeIcon() {
            const themeToggles = document.querySelectorAll('.theme-toggle');
            if (!themeToggles.length) return;

            const theme = document.documentElement.getAttribute('data-theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const effectiveTheme = theme || (prefersDark ? 'dark' : 'light');

            themeToggles.forEach(toggle => {
                toggle.setAttribute('data-mode', effectiveTheme);
                toggle.setAttribute(
                    'aria-label',
                    effectiveTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
                );
            });
        }

        // Mobile menu toggle
        function toggleMobileMenu() {
            const navLinks = document.querySelector('.nav-links');
            const menuToggle = document.querySelector('.mobile-menu-toggle');

            navLinks.classList.toggle('active');
            menuToggle.classList.toggle('active');
        }

        // Intersection Observer for scroll animations
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize theme
            initTheme();

            // Dark mode toggle
            document.querySelectorAll('.theme-toggle').forEach(toggle => {
                toggle.addEventListener('click', toggleTheme);
            });

            // Mobile menu toggle
            const menuToggle = document.querySelector('.mobile-menu-toggle');
            if (menuToggle) {
                menuToggle.addEventListener('click', toggleMobileMenu);
            }

            // Close mobile menu when clicking nav links
            document.querySelectorAll('.nav-links a').forEach(link => {
                link.addEventListener('click', function() {
                    if (window.innerWidth <= 768) {
                        toggleMobileMenu();
                    }
                });
            });

            // Scroll animations with improved performance
            const observerOptions = {
                threshold: 0.15,
                rootMargin: '0px 0px -100px 0px'
            };

            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-visible');
                        // Unobserve after animation to improve performance
                        observer.unobserve(entry.target);
                    }
                });
            }, observerOptions);

            // Observe all elements with scroll animation classes
            document.querySelectorAll('.scroll-animate, .scroll-fade-left, .scroll-fade-right, .scroll-scale').forEach(el => {
                observer.observe(el);
            });

            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
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

            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                    updateThemeIcon();
                }
            });
        });

        // Optimize scroll performance
        let ticking = false;
        window.addEventListener('scroll', function() {
            if (!ticking) {
                window.requestAnimationFrame(function() {
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
