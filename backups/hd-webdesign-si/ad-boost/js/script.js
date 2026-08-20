// Form submission for pilot signup
document.addEventListener('DOMContentLoaded', function() {
    const pilotForm = document.getElementById('pilot-form');
    const successMessage = document.getElementById('success-message');
    
    if (pilotForm) {
        pilotForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Basic validation
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            
            if (!name || !email) {
                alert('Please fill in required fields: Name and Email');
                return;
            }
            
            // In a real app, you would send data to a backend
            // For MVP, we'll simulate a successful submission
            
            // Show success message
            pilotForm.style.display = 'none';
            successMessage.style.display = 'block';
            
            // In a real implementation, you would:
            // 1. Send data to Netlify function or Gumroad webhook
            // 2. Redirect to Gumroad checkout for Pro plans
            // 3. Send confirmation email
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#' || href === '#signup') return; // Don't scroll for signup anchor
            
            e.preventDefault();
            const targetId = href.substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Mockup generate button interaction
    const generateBtn = document.querySelector('.mockup-generate');
    if (generateBtn) {
        generateBtn.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            this.disabled = true;
            
            // Simulate AI generation delay
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
                
                // Show a toast notification
                const toast = document.createElement('div');
                toast.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #10b981;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    z-index: 1000;
                    font-weight: 500;
                `;
                toast.innerHTML = '✓ Ad copy generated successfully!';
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 3000);
            }, 1500);
        });
    }
});