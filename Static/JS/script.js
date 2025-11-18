//just an ajax helper that allows the user to continue using other features from the website without it freezing
async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}
//this function is responsible for the color indicator according to the congestion percentage
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

//the modal is just the popup that we get after checking the congestion level
function showModal(data) {
  document.getElementById("modalTitle").textContent = data.location;
  document.getElementById("modalLevel").textContent = data.level;
  document.getElementById("modalPeople").textContent = data.average_people;
  document.getElementById("modalCapacity").textContent = data.capacity;
  document.getElementById("modalPercent").textContent = data.percent;

  document.getElementById("modal").classList.remove("hidden");

  //you get the google maps location both in the nomral spaces and the popup for better usability
  document.getElementById("directionsBtn").onclick = () => {
    const origin = prompt("Enter your starting location (optional):");
    let url =
      "https://www.google.com/maps/dir/?api=1&destination=" +
      encodeURIComponent(data.address || data.location);

    if (origin) url += "&origin=" + encodeURIComponent(origin);
    window.open(url, "_blank");
  };
}

function hideModal() {
  document.getElementById("modal").classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  //hover effect
  document.querySelectorAll(".space-card").forEach((card) => {
    card.addEventListener("mouseenter", () => {
      card.classList.add("ring-2", "ring-teal-400");
    });
    card.addEventListener("mouseleave", () => {
      card.classList.remove("ring-2", "ring-teal-400");
    });
  });

  //check button that runs yolo detecting the actual congestion level that is stored in the sql db
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
        if (json.error) return alert(json.error);

        colorIndicator(indicator, json.level);
        congSpan.textContent = json.level;
        timeSpan.textContent = new Date().toLocaleString();

        showModal(json);
        ev.currentTarget.textContent = "Check Again";
      } catch (err) {
        alert("Request failed: " + err.message);
      } finally {
        ev.currentTarget.disabled = false;
      }
    });
  });

  //another check button that I added but only checks the db for the latest congestion check the user made
  document.querySelectorAll(".prev-btn").forEach((btn) => {
    btn.addEventListener("click", async (ev) => {
      const loc = ev.currentTarget.dataset.loc;

      try {
        const json = await postJSON("/api/get_last_status", { location: loc });
        if (json.error) return alert(json.error);

        showModal(json);
      } catch (err) {
        alert("Failed: " + err.message);
      }
    });
  });

  //closing the popup
  document.getElementById("modalClose").addEventListener("click", hideModal);
  document.getElementById("modal").addEventListener("click", (e) => {
    if (e.target.id === "modal") hideModal();
  });
});
