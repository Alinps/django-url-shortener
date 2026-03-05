document.addEventListener("DOMContentLoaded",()=>{
    const toggles=document.querySelectorAll(".toggle-password");
    toggles.forEach(toggle=>{
        toggle.addEventListener("click",()=>{
            const input=toggle.previousElementSibling;
            const svg = toggle.querySelector("svg");
            if(input.type==="password"){
                input.type="text";
                svg.innerHTML = `
                    <path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a21.84 21.84 0 0 1 5.06-6.06"/>
                    <path d="M1 1l22 22"/>
                    <path d="M9.53 9.53A3.5 3.5 0 0 0 12 15.5a3.5 3.5 0 0 0 2.47-5.97"/>`;

            }else{
                input.type="password";
                svg.innerHTML = `
                    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/>
                    <circle cx="12" cy="12" r="3"/>`;
            }
        })
    })
})