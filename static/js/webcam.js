document.addEventListener('DOMContentLoaded', function() {
    const videoStream = document.getElementById('video-stream');
    const startWebcamBtn = document.getElementById('start-webcam');
    const stopWebcamBtn = document.getElementById('stop-webcam');
    const loadingSpinner = document.getElementById('loading-spinner');
    const webcamStatus = document.getElementById('webcam-status');

    // Show status message
    function showStatus(element, message, type) {
        element.textContent = message;
        element.className = 'status-message ' + type;
        setTimeout(() => {
            element.className = 'status-message';
        }, 5000);
    }

    // Show loading spinner
    function showSpinner(message = 'Loading...') {
        loadingSpinner.querySelector('.spinner-text').textContent = message;
        loadingSpinner.classList.add('active');
    }

    // Hide loading spinner
    function hideSpinner() {
        loadingSpinner.classList.remove('active');
    }

    // Start webcam
    startWebcamBtn.addEventListener('click', async () => {
        showSpinner('Starting webcam...');

        try {
            const response = await fetch('/start_webcam');
            if (response.ok) {
                videoStream.src = "/webcam_feed?" + new Date().getTime();
                startWebcamBtn.disabled = true;
                stopWebcamBtn.disabled = false;
                showStatus(webcamStatus, 'Webcam started successfully', 'success');
            } else {
                showStatus(webcamStatus, 'Failed to start webcam', 'error');
            }
        } catch (error) {
            console.error('Error starting webcam:', error);
            showStatus(webcamStatus, 'An error occurred. Please try again.', 'error');
        } finally {
            hideSpinner();
        }
    });

    // Stop webcam
    stopWebcamBtn.addEventListener('click', async () => {
        try {
            await fetch('/stop_webcam');
            videoStream.src = "/placeholder_feed";
            startWebcamBtn.disabled = false;
            stopWebcamBtn.disabled = true;
            showStatus(webcamStatus, 'Webcam stopped', 'info');
        } catch (error) {
            console.error('Error stopping webcam:', error);
        }
    });

    // Clean up when leaving the page
    window.addEventListener('beforeunload', () => {
        fetch('/stop_webcam');
    });
});