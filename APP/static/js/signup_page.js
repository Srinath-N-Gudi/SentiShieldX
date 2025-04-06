// ===== [ Password Toggle ] =====
document.querySelector('.toggle-password').addEventListener('click', function() {
	const passwordInput = this.previousElementSibling;
	const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
	passwordInput.setAttribute('type', type);
	this.classList.toggle('fa-eye-slash');
	this.style.color = type === 'text' ? '#d27b7b' : '#aaa';
});

// ===== [ Particle Animation ] =====
function createParticles() {
	const container = document.getElementById('particles');
	const particleCount = Math.floor(window.innerWidth / 10);

	for (let i = 0; i < particleCount; i++) {
		const particle = document.createElement('div');
		particle.classList.add('particle');

		// Random properties
		const size = Math.random() * 5 + 1;
		const posX = Math.random() * 100;
		const duration = Math.random() * 20 + 10;
		const delay = Math.random() * 10;

		particle.style.width = `$ {size} px`;
		particle.style.height = `$ {size} px`;
		particle.style.left = `$ {posX}%`;
		particle.style.opacity = Math.random() * 0.5 + 0.1;
		particle.style.animationDuration = `$ {duration} s`;
		particle.style.animationDelay = `$ {delay} s`;

		container.appendChild(particle);
	}
}
// Initialize
createParticles();
window.addEventListener('resize', createParticles);