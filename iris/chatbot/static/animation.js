// JavaScript for breathing animation
document.getElementById('play-animation').addEventListener('click', () => {
  const container = document.getElementById('animation-container');
  container.style.display = container.style.display === 'block' ? 'none' : 'block';
});

