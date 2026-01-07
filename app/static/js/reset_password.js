document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("resetForm");
  const password = document.getElementById("password");
  const confirmPassword = document.getElementById("confirm_password");
  const errorText = document.getElementById("matchError");

  form.addEventListener("submit", (e) => {
    if (password.value !== confirmPassword.value) {
      e.preventDefault();
      errorText.textContent = "Passwords do not match.";
      confirmPassword.focus();
    } else {
      errorText.textContent = "";
    }
  });
});
