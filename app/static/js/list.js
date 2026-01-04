const icon = document.getElementById("toggleIcon")
console.log(icon)
icon.addEventListener("click",()=>{
    icon.classList.toggle("active");
});