function openLogoutModal() {
    document.getElementById("logoutModal").classList.remove("hidden");
}

function closeLogoutModal() {
    document.getElementById("logoutModal").classList.add("hidden");
}

const logoutModal = document.getElementById("logoutModal");

logoutModal.addEventListener("click", function (event) {
    if (event.target === logoutModal) {
        closeLogoutModal();
    }
});