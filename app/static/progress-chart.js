// Links work without JavaScript; this only adds hover and keyboard previews.
document.querySelectorAll('.knowledge-map').forEach(map => {
  const title = map.querySelector('[data-map-title]');
  const score = map.querySelector('[data-map-score]');
  map.querySelectorAll('[data-topic]').forEach(link => {
    const preview = () => {
      title.textContent = link.dataset.topic;
      score.textContent = link.dataset.score;
    };
    link.addEventListener('mouseenter', preview);
    link.addEventListener('focus', preview);
  });
});
