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
function openEdit(id, title, url,isActive) {
  document.getElementById("edit-id").value = id;
  document.getElementById("edit-title").value = title;
  document.getElementById("edit-url").value = url;
  document.getElementById("edit-status").value = isActive === "True" ? "true" : "false";

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
      is_active: document.getElementById("edit-status").value
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      updateRowUI(id, data);
      closeEdit();
    }
  });
});



//update the ui
function updateRowUI(id, data) {
  const row = document.getElementById(`row-${id}`);

  // Update title & URL
  row.querySelector(".title").textContent = data.title;
  row.querySelector(".original").textContent = data.original_url;

  // Update status pill
  const statusSpan = row.querySelector(".status-pill");

  if (data.is_active) {
    statusSpan.textContent = "Active";
    statusSpan.classList.remove("disabled");
    statusSpan.classList.add("active");
  } else {
    statusSpan.textContent = "Disabled";
    statusSpan.classList.remove("active");
    statusSpan.classList.add("disabled");
  }
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
      document.getElementById(`row-${deleteId}`).remove();

    }
  });
}


//ajax search logic

const suggestionsBox = document.getElementById("suggestions");
const tableBody = document.getElementById("url-table-body");

let debounceTimer;

searchInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);

  debounceTimer = setTimeout(() => {
    const query = searchInput.value.trim();

    if (!query) {
      suggestionsBox.innerHTML = "";
      suggestionsBox.classList.remove("show");

    }

    fetch(`/search/?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        renderSuggestions(data.results);
        renderTableRows(data.results);
      });
  });
});

function renderSuggestions(results) {
  suggestionsBox.innerHTML = "";

  if (results.length === 0) {
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


function renderTableRows(results) {
  tableBody.innerHTML = "";

  if (results.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center;">No link to show.</td>
      </tr>
    `;
    return;
  }

  results.forEach(url => {
    tableBody.innerHTML += `
      <tr id="row-${url.id}">
        <td data-label="Short Link">
          <a href="/redirect/${url.short_code}">
            ${url.short_code}
          </a>
        </td>

        <td data-label="Title" class="title">${url.title}</td>

        <td data-label="Original URL" class="original">
          ${url.original_url}
        </td>

        <td data-label="Clicks">${url.click_count}</td>

        <td data-label="Status">
          <span class="status status-pill ${url.is_active ? "active" : "disabled"}">
            ${url.is_active ? "Active" : "Disabled"}
          </span>
        </td>

        <td data-label="Actions">
          <a href="/toggle/${url.id}" class="icon-btn">⏻</a>
          <a onclick="openEdit('${url.id}','${url.title}','${url.original_url}','${url.is_active}')" class="icon-btn edit">📝</a>
          <a onclick="openDelete('${url.id}')" class="icon-btn delete">🗑</a>
          <a class="icon-btn link"
             data-url="${window.location.origin}/redirect/${url.short_code}"
             onclick="copyToClipboard(this)">🔗</a>
        </td>
      </tr>
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

