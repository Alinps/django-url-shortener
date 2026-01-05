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


const searchToggle = document.getElementById("searchToggle");
const searchForm = document.getElementById("searchForm");
const searchInput = searchForm.querySelector("input");

searchToggle.addEventListener("click", () => {
  searchForm.classList.toggle("hidden");

  if (!searchForm.classList.contains("hidden")) {
    searchInput.focus();
  }
});

// Optional: ESC key hides search
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    searchForm.classList.add("hidden");
  }
});
