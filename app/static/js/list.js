function copyToClipboard(button){
    const textToCopy=button.getAttribute("data-url");
    navigator.clipboard.writeText(textToCopy)
        .then(()=>{
            alert("URL Coppied to Clipboard");
        })
        .catch((err)=>{
            console.log("Failed to copy: ",err);
            alert("Copy failed");
        })
}


// const searchToggle = document.getElementById("searchToggle");
const searchForm = document.getElementById("searchForm");
const searchInput = searchForm.querySelector("input");
//
// searchToggle.addEventListener("click", () => {
//   searchForm.classList.toggle("hidden");
//
//   if (!searchForm.classList.contains("hidden")) {
//     searchInput.focus();
//   }
// });
//
// // Optional: ESC key hides search
// document.addEventListener("keydown", (e) => {
//   if (e.key === "Escape") {
//     searchForm.classList.add("hidden");
//   }
// });


//logic for edit modal
function openEdit(id, title, url) {
  document.getElementById("edit-id").value = id;
  document.getElementById("edit-title").value = title;
  document.getElementById("edit-url").value = url;
  // document.getElementById("edit-status").value = isActive === "True" ? "true" : "false";

  document.getElementById("editModal").style.display = "flex";
}

function closeEdit() {
  document.getElementById("editModal").style.display = "none";
}

//logic for edit ajax
document.getElementById("editForm").addEventListener("submit", function(e) {
  e.preventDefault();

  const id = document.getElementById("edit-id").value;

  fetch(`/update/${id}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      title: document.getElementById("edit-title").value,
      original_url: document.getElementById("edit-url").value,
      // is_active: document.getElementById("edit-status").value
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      updateRowUI(id, data);
      showToast("URL updated successfully ✨", "success");
      closeEdit();

    }
    else{
       showToast("Failed to update URL", "error");
    }
  });
});



//update the ui
function updateRowUI(id, data) {
  const row = document.getElementById(`card-${id}`);

  // Update title & URL
  row.querySelector(".title").textContent = data.title;
  row.querySelector(".original").textContent = data.original_url;

  // Update status pill
  // const statusSpan = row.querySelector(".status-pill");

  // if (data.is_active) {
  //   statusSpan.textContent = "Active";
  //   statusSpan.classList.remove("disabled");
  //   statusSpan.classList.add("active");
  // } else {
  //   statusSpan.textContent = "Disabled";
  //   statusSpan.classList.remove("active");
  //   statusSpan.classList.add("disabled");
  // }
}


//logic for delete modal
let deleteId = null;

function openDelete(id) {
  deleteId = id;
  document.getElementById("deleteModal").style.display = "flex";
}

function closeDelete() {
  document.getElementById("deleteModal").style.display = "none";
}

//logic for delete ajax
function confirmDelete() {
  fetch(`/delete/${deleteId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      document.getElementById("deleteModal").style.display = "none";
      document.getElementById(`card-${deleteId}`).remove();
      document.getElementById("active_urls").textContent=data.active_urls;
      document.getElementById("disabled_urls").textContent=data.disabled_urls;
      document.getElementById("total_urls").textContent=data.total_urls;
      showToast("URL deleted 🗑️", "success");

    }else{
      showToast("Delete failed", "error");
    }
  });
}


//ajax search logic
// ========================
// DOM ELEMENTS
// ========================

function formatDate(dateString) {
  const date = new Date(dateString);

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "2-digit",
    year: "numeric"
  });
}


const suggestionsBox = document.getElementById("suggestions");
const urlCardContainer = document.getElementById("urlCardContainer");

let debounceTimer;

// Store original cards (Django-rendered)
const originalCardsHTML = urlCardContainer.innerHTML;


// ========================
// SEARCH INPUT HANDLER
// ========================
searchInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);

  debounceTimer = setTimeout(() => {
    const query = searchInput.value.trim();

    // 🔄 Restore original cards when input is empty
    if (!query) {
      suggestionsBox.innerHTML = "";
      suggestionsBox.classList.remove("show");
      urlCardContainer.innerHTML = originalCardsHTML;
      return;
    }

    fetch(`/search/?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        renderSuggestions(data.results);
        renderCards(data.results);
      })
      .catch(err => {
        console.error("Search error:", err);
      });

  }, 300); // debounce delay
});


// ========================
// SUGGESTIONS DROPDOWN
// ========================
function renderSuggestions(results) {
  suggestionsBox.innerHTML = "";

  if (!results || results.length === 0) {
    suggestionsBox.classList.remove("show");
    return;
  }

  results.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item.title;

    li.onclick = () => {
      searchInput.value = item.title;
      suggestionsBox.innerHTML = "";
      suggestionsBox.classList.remove("show");
    };

    suggestionsBox.appendChild(li);
  });

  suggestionsBox.classList.add("show");
}


// ========================
// CARD RENDERING
// ========================
function renderCards(results) {
  urlCardContainer.innerHTML = ""; // 🔥 clear before rendering

  if (!results || results.length === 0) {
    urlCardContainer.innerHTML = `
      <div class="url-card">
        <p>No link to show.</p>
      </div>
    `;
    return;
  }

  results.forEach(url => {
    urlCardContainer.innerHTML += `
      <div class="url-card" id="card-${url.id}">

        <!-- Title -->
        <div class="cell cell-title">
          <img src="https://www.google.com/s2/favicons?domain=${url.original_url}" alt="">
          <span>${url.title}</span>
        </div>

        <!-- URLs -->
        <div class="cell cell-links">
          <a href="/redirect/${url.short_code}" class="short-link">
            ${window.location.origin}/${url.short_code}
          </a>
          <span class="original-url">${url.original_url}</span>
        </div>

        <!-- Date -->
        <div class="cell cell-date">
          📅 ${formatDate(url.created_at)}
        </div>

        <!-- Clicks -->
        <div class="cell cell-clicks">
          👁 ${url.click_count}
        </div>

        <!-- Status -->
        <div class="cell cell-status">
          <span
            class="status-pill ${url.is_active ? "active" : "disabled"}"
            id="toggleStatus_${url.id}">
            ${url.is_active ? "Active" : "Disabled"}
          </span>
        </div>

        <!-- Actions -->
        <div class="cell cell-actions">
          <span class="icon-btn ${url.is_active ? "active" : ""}"
                onclick="toggleStatus('${url.id}')">⏻</span>

          <span class="icon-btn edit"
                onclick="openEdit('${url.id}','${url.title}','${url.original_url}')">📝</span>

          <span class="icon-btn delete"
                onclick="openDelete('${url.id}')">🗑</span>

          <span class="icon-btn copy"
                data-url="${window.location.origin}/redirect/${url.short_code}"
                onclick="copyToClipboard(this)">📋</span>
        </div>

      </div>
    `;
  });
}

document.addEventListener("click", (e) => {
  if (!e.target.closest(".search-wrapper")) {
    suggestionsBox.classList.remove("show");
  }
});
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    suggestionsBox.classList.remove("show");
    searchInput.blur();
  }
});

function toggleStatus(id) {
  fetch(`/togglestatusajax/${id}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
    }
  })
  .then(res => res.json())
  .then(data => {
    const statusEl = document.getElementById(`toggleStatus_${id}`);

    if (data.status) {
      statusEl.textContent = "Active";
      statusEl.classList.add("active");
      statusEl.classList.remove("disabled");
    } else {
      statusEl.textContent = "Disabled";
      statusEl.classList.remove("active");
      statusEl.classList.add("disabled");
    }

    document.getElementById('active_urls').textContent = data.active_url;
    document.getElementById('disabled_urls').textContent = data.disabled_url;
  });
}



//share modal logic
let activeShareUrl = "";

function openShare(el) {
  activeShareUrl = el.dataset.url;
  const encoded = encodeURIComponent(activeShareUrl);

  document.getElementById("share-whatsapp").href =
    `https://wa.me/?text=${encoded}`;

  document.getElementById("share-x").href =
    `https://twitter.com/intent/tweet?url=${encoded}`;

  document.getElementById("share-linkedin").href =
    `https://www.linkedin.com/sharing/share-offsite/?url=${encoded}`;

  document.getElementById("share-facebook").href =
    `https://www.facebook.com/sharer/sharer.php?u=${encoded}`;

  document.getElementById("share-overlay").classList.remove("hidden");
  document.getElementById("share-card").classList.remove("hidden");
}

function closeShare() {
  document.getElementById("share-overlay").classList.add("hidden");
  document.getElementById("share-card").classList.add("hidden");
}

function copyShareLink() {
  navigator.clipboard.writeText(activeShareUrl);
  closeShare();
  alert("Link copied to clipboard");
}


//url click count status increment
//

function updateDashboardStats() {
  fetch("/dashboard/stats/")
    .then(res => res.json())
    .then(data => {
      // Update total clicks
      const totalEl = document.getElementById("total");
      if (totalEl) {
        totalEl.innerText = data.total_clicks;
      }

      // Update each URL click count
      for (const [urlId, clickCount] of Object.entries(data.urls)) {
        const el = document.getElementById(`click-count-${urlId}`);
        if (el) {
          el.innerText = clickCount;
        }
      }
    })
    .catch(err => {
      console.error("Dashboard polling failed", err);
    });
}

// Poll every 5 seconds
setInterval(updateDashboardStats, 5000);



//toast logic
function showToast(message, type = "info", duration = 3000) {
  const container = document.getElementById("toastContainer");

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="toast-close">&times;</button>
  `;

  container.appendChild(toast);

  toast.querySelector(".toast-close").onclick = () => toast.remove();

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}