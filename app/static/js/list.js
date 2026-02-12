


//logic for edit modal
function openEdit(id) {
   fetch(`/update/${id}`)
   .then(res => res.json())
   .then(data =>{
   console.log(data)
        document.getElementById("edit-id").value = data.id;
        document.getElementById("edit-title").value = data.title;
        document.getElementById("edit-url").value = data.original_url;
        document.getElementById("edit-short_code").value = data.custom_url
   })


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
    method: "PUT",
    headers: {
      "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      title: document.getElementById("edit-title").value,
      original_url: document.getElementById("edit-url").value,
      custom_code:document.getElementById("edit-short_code").value,
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
       showToast(`Failed to update URL, ${data.message}` , "error");
    }
  });
});



//update the ui
function updateRowUI(id, data) {
  const row = document.getElementById(`card-${id}`);
  const shortUrl = `${BASE_URL}/${data.custom_url}`;
  const shortUrlEl = document.getElementById(`short-url-${id}`);

  // Update title & URL
  row.querySelector(".title").textContent = data.title;
  row.querySelector(".original").textContent = data.original_url;
  shortUrlEl.href = shortUrl;
  shortUrlEl.innerHTML = shortUrl;
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
    method: "DELETE",
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





function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie("csrftoken");




function toggleStatus(id) {
  fetch(`/togglestatusajax/${id}`, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken
        }
  })
  .then(res => res.json())
  .then(data => {
  console.log(data)
    const statusEl = document.getElementById(`toggleStatus_${id}`);
if (data.success){
 if (data.status) {
      statusEl.textContent = "Active";
      statusEl.classList.add("active");
      statusEl.classList.remove("disabled");
    } else {
      statusEl.textContent = "Disabled";
      statusEl.classList.remove("active");
      statusEl.classList.add("disabled");
    }

    document.getElementById('active_urls').textContent = data.active_count;
    document.getElementById('disabled_urls').textContent = data.disabled_count;
    showToast("Status changed successfully","success");
}else{
    showToast("Status not changed","error");
}

  });
}



//share modal logic
let activeUrlId = null;

function openShare(urlId) {
  activeUrlId = urlId;

  const linkEl = document.getElementById(`short-url-${urlId}`);
  if (!linkEl) return;

  const activeShareUrl = linkEl.href;
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
  if (!activeUrlId) return;

  const linkEl = document.getElementById(`short-url-${activeUrlId}`);
  if (!linkEl) return;

  navigator.clipboard.writeText(linkEl.href);
  closeShare();
  showToast("Link copied 📋", "success");
}



//url click count status increment

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




// Poll every
let statsInterval;

function startPolling() {
  statsInterval = setInterval(updateDashboardStats, 15000);
}

function stopPolling() {
  clearInterval(statsInterval);
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopPolling();
  } else {
    startPolling();
  }
});

startPolling();




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










const searchInput = document.querySelector('input[name="q"]');
const urlContainer = document.getElementById("urlCardContainer");
const paginationContainer = document.querySelector(".pagination");

let debounceTimer;
let currentPage = 1;
let controller;
function fetchResults(query = "", page = 1) {

  if (controller) controller.abort();
  controller = new AbortController();

  fetch(`/list/?q=${encodeURIComponent(query)}&page=${page}`, {
    headers: { "X-Requested-With": "XMLHttpRequest" },
    signal: controller.signal
  })
    .then(res => res.json())
    .then(data => {
      renderCards(data.results);
      renderPagination(data.pagination, query);
      updateStats(data.stats);

      // Update URL without reload
      history.pushState(null, "", `?q=${query}&page=${page}`);
    })
    .catch(err => console.error("Search error:", err));
}


function renderCards(results) {
  urlContainer.innerHTML = "";

  if (!results.length) {
    urlContainer.textContent = "No links found.";
    return;
  }

  results.forEach(url => {

    const card = document.createElement("div");
    card.className = "url-card";

    card.innerHTML = `
      <div class="cell cell-title">
        <img src="https://www.google.com/s2/favicons?domain=${url.original_url}">
        <span>${url.title}</span>
      </div>

      <div class="cell cell-links">
        <a href="${BASE_URL}/${url.short_code}" target="_blank">
          ${BASE_URL}/${url.short_code}
        </a>
        <span class="original-url">${url.original_url}</span>
      </div>

      <div class="cell cell-date">
        ${url.created_at}
      </div>

      <div class="cell cell-clicks">
        👁 ${url.click_count}
      </div>

      <div class="cell cell-status">
        <span class="status-pill ${url.is_active ? "active" : "disabled"}">
          ${url.is_active ? "Active" : "Disabled"}
        </span>
      </div>
    `;

    urlContainer.appendChild(card);
  });
}




function renderPagination(pagination, query) {

  paginationContainer.innerHTML = "";

  if (pagination.has_previous) {
    const prev = document.createElement("button");
    prev.textContent = "← Previous";
    prev.onclick = () => fetchResults(query, pagination.current_page - 1);
    paginationContainer.appendChild(prev);
  }

  const info = document.createElement("span");
  info.textContent = `Page ${pagination.current_page} of ${pagination.total_pages}`;
  paginationContainer.appendChild(info);

  if (pagination.has_next) {
    const next = document.createElement("button");
    next.textContent = "Next →";
    next.onclick = () => fetchResults(query, pagination.current_page + 1);
    paginationContainer.appendChild(next);
  }
}



function updateStats(stats) {
  document.getElementById("total_urls").textContent = stats.total_urls;
  document.getElementById("active_urls").textContent = stats.active_urls;
  document.getElementById("disabled_urls").textContent = stats.disabled_urls;
  document.getElementById("total").textContent = stats.total_clicks;
}


searchInput.addEventListener("input", () => {

  clearTimeout(debounceTimer);

  debounceTimer = setTimeout(() => {
    currentPage = 1;
    fetchResults(searchInput.value.trim(), 1);
  }, 300);
});
