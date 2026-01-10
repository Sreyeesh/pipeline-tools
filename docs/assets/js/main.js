const reveal = () => {
  const nodes = document.querySelectorAll('.feature, .install-card, .flow-step, .doc-card');
  const trigger = window.innerHeight * 0.85;
  nodes.forEach((node) => {
    const rect = node.getBoundingClientRect();
    if (rect.top < trigger) {
      node.classList.add('is-visible');
    }
  });
};

window.addEventListener('scroll', reveal, { passive: true });
window.addEventListener('load', reveal);
