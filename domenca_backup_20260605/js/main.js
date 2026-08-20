// Theme toggle
const themeToggle = document.getElementById('themeToggle');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

function setTheme(isDark) {
    document.body.classList.toggle('dark-mode', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    themeToggle.innerHTML = isDark ? '☀️' : '🌙';
}

function toggleTheme() {
    const isDark = !document.body.classList.contains('dark-mode');
    setTheme(isDark);
}

// Initialize theme
const savedTheme = localStorage.getItem('theme');
const initialTheme = savedTheme === 'dark' || (!savedTheme && prefersDark.matches);
setTheme(initialTheme);

themeToggle.addEventListener('click', toggleTheme);

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        const target = document.querySelector(targetId);
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Contact form handling (if present)
const contactForm = document.getElementById('contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = contactForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';
        
        // Simulate sending
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        alert('Message sent! (This is a demo)');
        contactForm.reset();
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    });
}