// ===============================
// drag-drop.js
// Drag & drop with hover highlight for same-division tables
// ===============================

// AJAX request to swap matches
function send_request(matchOne_id, matchTwo_id) {
  if (!matchOne_id || !matchTwo_id) return;
  $.ajax({
    type: "GET",
    url: `/task-assign/${matchOne_id}/${matchTwo_id}/`,
    success: function (data) {
      console.log("Swap successful:", matchOne_id, matchTwo_id);
    },
    error: function (data) {
      console.log("Swap failed", data);
    },
  });
}

// Highlight valid drop targets in the same table
function highlightTable(table, enable) {
  if (!table) return;
  const cells = table.querySelectorAll(".float-child");
  cells.forEach((cell) => {
    if (enable) {
      cell.classList.add("valid-drop");
    } else {
      cell.classList.remove("valid-drop");
      cell.classList.remove("hovered-cell"); // remove hover when dragging ends
    }
  });
}

// Add hover highlight for potential drop target
function addHoverEffect(cell, table) {
  cell.addEventListener("dragenter", () => {
    if (table.dragging && cell !== table.dragging) {
      cell.classList.add("hovered-cell");
    }
  });
  cell.addEventListener("dragleave", () => {
    cell.classList.remove("hovered-cell");
  });
}

// Attach drag-drop events to a single match cell
function addEventsToCell(cell, table) {
  if (!cell || !table) return;

  cell.setAttribute("draggable", "true");

  cell.addEventListener("dragstart", (ev) => {
    table.dragging = ev.currentTarget;
    if (table.dragging) table.dragging.classList.add("dragging");

    // Highlight all cells in this table as valid drop targets
    highlightTable(table, true);
  });

  cell.addEventListener("dragend", (ev) => {
    if (table.dragging) table.dragging.classList.remove("dragging");
    table.dragging = null;

    // Remove highlights
    highlightTable(table, false);
  });

  cell.addEventListener("dragover", (ev) => ev.preventDefault());

  cell.addEventListener("drop", (ev) => {
    ev.preventDefault();

    const target = ev.currentTarget;
    const dragging = table.dragging;

    if (!dragging || !target) return;

    const dragTable = dragging.closest("table");
    const targetTable = target.closest("table");
    if (!dragTable || !targetTable || dragTable !== targetTable) return;

    const dragClone = dragging.cloneNode(true);
    const targetClone = target.cloneNode(true);

    const dragId = dragging.id;
    const targetId = target.id;
    if (!dragId || !targetId) return;

    // AJAX swap
    send_request(dragId, targetId);

    // Swap elements in DOM
    target.replaceWith(dragClone);
    dragging.replaceWith(targetClone);

    // Reattach events to cloned elements
    addEventsToCell(dragClone, table);
    addEventsToCell(targetClone, table);

    table.dragging = null;

    // Remove highlights after drop
    highlightTable(table, false);
  });

  // Attach hover highlight events
  addHoverEffect(cell, table);
}

// Initialize drag-drop for all tables
function initDragDrop() {
  const tables = document.querySelectorAll("table");
  if (!tables || tables.length === 0) return;

  tables.forEach((table) => {
    table.dragging = null;

    const cells = table.querySelectorAll(".float-child");
    if (!cells) return;

    cells.forEach((cell) => addEventsToCell(cell, table));
  });
}

// Add CSS for hover highlight
const style = document.createElement("style");
style.innerHTML = `
  /* Hover highlight for potential drop target */
  .float-child.hovered-cell {
    outline: 2px solid #0a0a38ff;
    transition: background-color 0.2s, outline 0.2s;
  }
`;
document.head.appendChild(style);

// Run after DOM is loaded
window.addEventListener("DOMContentLoaded", initDragDrop);
