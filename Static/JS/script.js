// helper
async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

function colorIndicator(el, level) {
  if (!el) return;
  const colors = {
    Low: "#28a745",
    Medium: "#f6c34a",
    High: "#dc3545",
    Default: "#ffffff",
  };
  const color = colors[level] || colors.Default;
  el.style.background = color;
  el.style.borderColor = color;
}

function showModal(data) {
  const title = document.getElementById("modalTitle");
  const level = document.getElementById("modalLevel");
  const people = document.getElementById("modalPeople");
  const capacity = document.getElementById("modalCapacity");
  const percent = document.getElementById("modalPercent");
  const modal = document.getElementById("modal");
  if (title) title.textContent = data.location;
  if (level) level.textContent = data.level;
  if (people) people.textContent = data.average_people;
  if (capacity) capacity.textContent = data.capacity;
  if (percent) percent.textContent = data.percent;
  if (modal) modal.classList.remove("hidden");

  const directionsBtn = document.getElementById("directionsBtn");
  if (directionsBtn) {
    directionsBtn.onclick = () => {
      const origin = prompt("Enter your starting location (optional):");
      let url =
        "https://www.google.com/maps/dir/?api=1&destination=" +
        encodeURIComponent(data.address || data.location);
      if (origin) url += "&origin=" + encodeURIComponent(origin);
      window.open(url, "_blank");
    };
  }
}

function hideModal() {
  const modal = document.getElementById("modal");
  if (modal) modal.classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  // hover effect
  document.querySelectorAll(".space-card").forEach((card) => {
    card.addEventListener("mouseenter", () =>
      card.classList.add("ring-2", "ring-teal-400")
    );
    card.addEventListener("mouseleave", () =>
      card.classList.remove("ring-2", "ring-teal-400")
    );
  });

  // Check (YOLO)
  document.querySelectorAll(".check-btn").forEach((btn) => {
    btn.addEventListener("click", async (ev) => {
      const loc = ev.currentTarget.dataset.loc;
      const indicator = document.getElementById("indicator-" + loc);
      const congSpan = document.getElementById("cong-" + loc);
      const timeSpan = document.getElementById("time-" + loc);
      ev.currentTarget.disabled = true;
      ev.currentTarget.textContent = "Checking...";

      try {
        const json = await postJSON("/api/analyze", { location: loc });
        if (json.error) {
          alert(json.error);
        } else {
          colorIndicator(indicator, json.level);
          if (congSpan) congSpan.textContent = json.level;
          if (timeSpan) timeSpan.textContent = new Date().toLocaleString();
          showModal(json);
          ev.currentTarget.textContent = "Check Again";
        }
      } catch (err) {
        alert("Request failed: " + (err.message || err));
        ev.currentTarget.textContent = "Check";
      } finally {
        ev.currentTarget.disabled = false;
      }
    });
  });

  // View previous (from DB)
  document.querySelectorAll(".prev-btn").forEach((btn) => {
    btn.addEventListener("click", async (ev) => {
      const loc = ev.currentTarget.dataset.loc;
      try {
        const json = await postJSON("/api/get_last_status", { location: loc });
        if (json.error) return alert(json.error);
        showModal(json);
      } catch (err) {
        alert("Failed: " + (err.message || err));
      }
    });
  });

  // modal handlers
  const modalClose = document.getElementById("modalClose");
  if (modalClose) modalClose.addEventListener("click", hideModal);
  const modal = document.getElementById("modal");
  if (modal)
    modal.addEventListener("click", (e) => {
      if (e.target === modal) hideModal();
    });
});
