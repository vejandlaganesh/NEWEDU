/**
 * NEWEDU - Auth Pages JavaScript
 */
document.addEventListener('DOMContentLoaded', function () {

    // Password visibility toggle
    const toggle = document.getElementById('passwordToggle');
    if (toggle) {
        toggle.addEventListener('click', function () {
            const passwordInput = this.closest('.input-wrapper').querySelector('input');
            if (passwordInput) {
                const isPassword = passwordInput.type === 'password';
                passwordInput.type = isPassword ? 'text' : 'password';
                this.textContent = isPassword ? '◎' : '◉';
                this.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
            }
        });
    }

    // Auto-dismiss messages after 5 seconds
    const messages = document.querySelectorAll('.auth-message');
    messages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.transition = 'opacity 0.4s ease';
            msg.style.opacity = '0';
            setTimeout(function () { msg.remove(); }, 400);
        }, 5000);
    });

});
