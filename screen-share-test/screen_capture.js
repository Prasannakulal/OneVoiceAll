const startBtn = document.getElementById('start-share-btn');
const stopBtn = document.getElementById('stop-share-btn');
const videoEl = document.getElementById('local-video');

let screenStream = null;

// When the "Start" button is clicked
startBtn.addEventListener('click', async () => {
    console.log('Requesting screen capture...');
    try {
        // Use the browser's getDisplayMedia API to request screen access
        screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: true, // We want to capture video
            audio: false // We don't need to capture system audio for this test
        });

        console.log('Screen capture started successfully!');
        
        // Display the captured stream in our local video element
        videoEl.srcObject = screenStream;

        // Show the "Stop" button and hide the "Start" button
        startBtn.style.display = 'none';
        stopBtn.style.display = 'inline';

        // Add a listener to handle when the user clicks the browser's "Stop sharing" button
        screenStream.getVideoTracks()[0].addEventListener('ended', stopSharing);

    } catch (error) {
        console.error('Error starting screen capture:', error);
    }
});

// When the "Stop" button is clicked
stopBtn.addEventListener('click', () => {
    stopSharing();
});

function stopSharing() {
    if (screenStream) {
        // Stop all tracks in the stream
        screenStream.getTracks().forEach(track => track.stop());
        screenStream = null;
        videoEl.srcObject = null;
        
        console.log('Screen capture stopped.');

        // Reset the buttons
        startBtn.style.display = 'inline';
        stopBtn.style.display = 'none';
    }
}