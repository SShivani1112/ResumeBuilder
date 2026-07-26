/*
  Module 2 (client side): Resume Form interactivity.
  Lets the user add/remove repeating entries (education rows, skill rows,
  project rows, etc.) before submitting each section to the server.
*/

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-repeat-container]").forEach(initRepeatingSection);
});

function initRepeatingSection(container) {
  const template = container.querySelector("[data-template]");
  const addBtn = container.parentElement.querySelector("[data-add-btn]");

  const renumber = () => {
    const items = container.querySelectorAll(".repeat-item");
    items.forEach((item, index) => {
      const n = index + 1;
      item.querySelectorAll("[data-field]").forEach((input) => {
        const base = input.getAttribute("data-field");
        input.name = `${base}_${n}`;
      });
    });
  };

  container.querySelectorAll(".remove-item").forEach((btn) => bindRemove(btn, container, renumber));

  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const clone = template.content.firstElementChild.cloneNode(true);
      const removeBtn = clone.querySelector(".remove-item");
      bindRemove(removeBtn, container, renumber);
      container.appendChild(clone);
      renumber();
    });
  }
}

function bindRemove(btn, container, renumber) {
  if (!btn) return;
  btn.addEventListener("click", () => {
    const item = btn.closest(".repeat-item");
    const items = container.querySelectorAll(".repeat-item");
    if (items.length > 1) {
      item.remove();
      renumber();
    } else {
      // Keep at least one row, just clear its inputs
      item.querySelectorAll("input, textarea").forEach((el) => (el.value = ""));
    }
  });
}

/* Simple client-side preview of an uploaded profile photo */
function previewPhoto(input) {
  const preview = document.getElementById("photo-preview");
  if (!preview || !input.files || !input.files[0]) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    preview.style.display = "block";
  };
  reader.readAsDataURL(input.files[0]);
}
