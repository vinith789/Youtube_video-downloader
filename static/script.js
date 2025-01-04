
const form = document.getElementById('download-form');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const statusText = document.getElementById('status');
const fileNameText = document.getElementById('file-name');
const speedText = document.getElementById('speed');
const downloadedSizeText = document.getElementById('downloaded-size');
const totalSizeText = document.getElementById('total-size');
const timeRemainingText = document.getElementById('time-remaining');

let progressInterval;
// Function to reset the progress display
function resetProgress() {
    progressBar.value = 0;
    statusText.textContent = 'Status: Idle';
    fileNameText.textContent = 'File: Unknown';
    speedText.textContent = 'Speed: 0 KB/s';
    downloadedSizeText.textContent = 'Downloaded: 0 MB';
    totalSizeText.textContent = 'Total Size: 0 MB';
    timeRemainingText.textContent = 'Time Remaining: 0s';
}

// Function to check if the video is already downloaded
async function checkIfAlreadyDownloaded(videoUrl, videoQuality) {
    try {
        const response = await fetch('/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ videoUrl, videoQuality }),
        });

        if (response.ok) {
            const data = await response.json();
            return data.exists; // Returns true if video exists, otherwise false
        } else {
            console.error('Error checking video status:', await response.text());
            return false;
        }
    } catch (error) {
        console.error('Error checking video status:', error);
        return false;
    }
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const videoUrl = document.getElementById('video-url').value;
    const videoQuality = document.getElementById('video-quality').value;

    resetProgress(); // Reset progress details before starting a new download
    progressContainer.style.display = 'block';
    statusText.textContent = 'Checking if video is already downloaded...';

    // Check if the video is already downloaded
    const alreadyDownloaded = await checkIfAlreadyDownloaded(videoUrl, videoQuality);

    if (alreadyDownloaded) {
        statusText.textContent = 'Video is already downloaded in the selected quality.';
        progressContainer.style.display = 'none';
        return;
    }

    statusText.textContent = 'Starting download...';

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ videoUrl, videoQuality }),
        });

        if (response.ok) {
            const data = await response.json();
            statusText.textContent = data.message;

            // Start polling progress for the new download
            clearInterval(progressInterval);
            progressInterval = setInterval(updateProgress, 1000);
        } else {
            const errorData = await response.json();
            statusText.textContent = `Download failed: ${errorData.message}`;
            clearInterval(progressInterval);
        }
    } catch (error) {
        statusText.textContent = `Error: ${error.message}`;
        clearInterval(progressInterval);
    }
});

// Fetch and update progress
function updateProgress() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            statusText.textContent = `Status: ${data.status}`;
            fileNameText.textContent = `File: ${data.file_name}`;
            speedText.textContent = `Speed: ${data.speed}`;
            downloadedSizeText.textContent = `Downloaded: ${data.downloaded_size}`;
            totalSizeText.textContent = `Total Size: ${data.total_size}`;
            timeRemainingText.textContent = `Time Remaining: ${data.time_remaining}`;
        });
}

// Start polling the progress endpoint
progressInterval = setInterval(updateProgress, 1000);