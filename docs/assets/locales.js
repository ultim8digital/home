/* Native details and ordinary links provide the complete no-JavaScript picker. */
(() => {
  const picker = document.querySelector('.language-picker');
  if (!picker) return;
  const summary = picker.querySelector('summary');
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && picker.open) {
      picker.open = false;
      summary.focus();
      event.preventDefault();
    }
  });
  document.addEventListener('click', (event) => {
    if (!picker.contains(event.target)) picker.open = false;
  });
  picker.addEventListener('focusout', (event) => {
    // Pointer activation can clear focus without focusing the link (Safari,
    // touch input). Keep its target visible until the click can navigate.
    const next = event.relatedTarget;
    if (next instanceof Node && !picker.contains(next)) picker.open = false;
  });
})();
