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