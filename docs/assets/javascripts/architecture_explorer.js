document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("details").forEach((element) => {
    element.addEventListener("toggle", () => {
      if (element.open) {
        element.dataset.openedAt = new Date().toISOString();
      }
    });
  });
});
