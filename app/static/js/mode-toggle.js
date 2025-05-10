const body = document.getElementById('body-root');
const toggleBtn = document.getElementById('toggle-mode');
const toggleIcon = document.getElementById('toggle-icon');
const toggleLabel = document.getElementById('toggle-label');

function setMode(mode) {
  if (mode === 'light') {
    body.classList.remove('dark');
    body.classList.add('light');
    toggleIcon.textContent = 'light_mode';
    toggleLabel.textContent = 'Light';
    toggleBtn.classList.remove('bg-[var(--offwhite)]', 'text-[var(--dark)]');
    toggleBtn.classList.add('bg-[var(--dark)]', 'text-[var(--offwhite)]');
  } else {
    body.classList.remove('light');
    body.classList.add('dark');
    toggleIcon.textContent = 'dark_mode';
    toggleLabel.textContent = 'Dark';
    toggleBtn.classList.remove('bg-[var(--dark)]', 'text-[var(--offwhite)]');
    toggleBtn.classList.add('bg-[var(--offwhite)]', 'text-[var(--dark)]');
  }
}

// Initial mode
let mode = 'dark';
setMode(mode);

toggleBtn.addEventListener('click', () => {
  mode = mode === 'dark' ? 'light' : 'dark';
  setMode(mode);
});
