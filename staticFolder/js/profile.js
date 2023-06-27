function handleFileInputChange(event) {
    const fileInput = event.target;
    const files = fileInput.files;
    const fileInputLabel = document.getElementById('fileInputLabel');

    if (files.length > 0) {
        fileInputLabel.textContent = files[0].name;
    } else {
        fileInputLabel.textContent = 'Edit';
    }
}

// Make a GET request to retrieve the image data for the current user
fetch('/image')
.then(response => response.blob())
.then(imageBlob => {
    // Create an object URL from the Blob
    var imageURL = URL.createObjectURL(imageBlob);

    // Set the image source
    var imageElement = document.getElementById('imageElement');
    imageElement.src = imageURL;
})
.catch(error => console.error(error));
