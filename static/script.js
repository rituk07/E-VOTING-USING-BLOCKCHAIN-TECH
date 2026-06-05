document.addEventListener("DOMContentLoaded", function () {

    const video = document.getElementById("video");

    // Start camera only if video element exists
    if (video) {
        navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.play();
        })
        .catch(err => {
            console.error("Camera Error:", err);
            alert("❌ Camera access denied or not available");
        });
    }

});

// Capture image
function capture() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const input = document.getElementById("image_data");

    if (!video || !canvas || !input) {
        alert("❌ Camera elements missing");
        return;
    }

    const ctx = canvas.getContext("2d");

    // Resize for performance
    canvas.width = 300;
    canvas.height = 300;

    ctx.drawImage(video, 0, 0, 300, 300);

    // Compress image
    const data = canvas.toDataURL("image/jpeg", 0.5);
    input.value = data;

    alert("✅ Face Captured Successfully");
}