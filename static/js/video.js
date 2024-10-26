document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('myVideo');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const centerPlayPauseBtn = document.getElementById('centerPlayPauseBtn');
    const backwardBtn = document.getElementById('backwardBtn');
    const forwardBtn = document.getElementById('forwardBtn');
    const seekBar = document.getElementById('seekBar');
    const muteBtn = document.getElementById('muteBtn');
    const volumeBtn = document.getElementById('volumeBtn');
    const volumeSlider = document.querySelector('.volume-slider');
    const volumeBar = document.getElementById('volumeBar');
    const currentTimeDisplay = document.getElementById('currentTime');
    const durationDisplay = document.getElementById('duration');

    const playIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="30px" height="30px" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.5" d="M3 12v6.967c0 2.31 2.534 3.769 4.597 2.648l3.203-1.742M3 8V5.033c0-2.31 2.534-3.769 4.597-2.648l12.812 6.968a2.998 2.998 0 0 1 0 5.294l-6.406 3.484"/></svg>';
    const pauseIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="30px" height="30px" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.5" d="M2 18c0 1.886 0 2.828.586 3.414C3.172 22 4.114 22 6 22c1.886 0 2.828 0 3.414-.586C10 20.828 10 19.886 10 18V6c0-1.886 0-2.828-.586-3.414C8.828 2 7.886 2 6 2c-1.886 0-2.828 0-3.414.586C2 3.172 2 4.114 2 6v8m20-8c0-1.886 0-2.828-.586-3.414C20.828 2 19.886 2 18 2c-1.886 0-2.828 0-3.414.586C14 3.172 14 4.114 14 6v12c0 1.886 0 2.828.586 3.414C15.172 22 16.114 22 18 22c1.886 0 2.828 0 3.414-.586C22 20.828 22 19.886 22 18v-8"/></svg>';

    // Check for duration and set it once it's available
    const checkDurationInterval = setInterval(() => {
        if (video.duration && !isNaN(video.duration)) {
            clearInterval(checkDurationInterval);

            const durationMinutes = Math.floor(video.duration / 60);
            const durationSeconds = Math.floor(video.duration % 60);
            durationDisplay.textContent = `${durationMinutes}:${durationSeconds < 10 ? '0' + durationSeconds : durationSeconds}`;
            console.log("Total duration set:", durationDisplay.textContent);

            // Attempt autoplay
            video.play().catch(error => {
                console.log("Autoplay was prevented. Click to play video:", error);
            });
        }
    }, 100); // Check every 100ms until duration is available

    // Play/Pause functionality
    function togglePlayPause() {
        if (video.paused) {
            video.play();
            playPauseBtn.innerHTML = pauseIcon;
            centerPlayPauseBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="50px" height="50px" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.5" d="M2 18c0 1.886 0 2.828.586 3.414C3.172 22 4.114 22 6 22c1.886 0 2.828 0 3.414-.586C10 20.828 10 19.886 10 18V6c0-1.886 0-2.828-.586-3.414C8.828 2 7.886 2 6 2c-1.886 0-2.828 0-3.414.586C2 3.172 2 4.114 2 6v8m20-8c0-1.886 0-2.828-.586-3.414C20.828 2 19.886 2 18 2c-1.886 0-2.828 0-3.414.586C14 3.172 14 4.114 14 6v12c0 1.886 0 2.828.586 3.414C15.172 22 16.114 22 18 22c1.886 0 2.828 0 3.414-.586C22 20.828 22 19.886 22 18v-8"/></svg>';
        } else {
            video.pause();
            playPauseBtn.innerHTML = playIcon;
            centerPlayPauseBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="50px" height="50px" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.5" d="M3 12v6.967c0 2.31 2.534 3.769 4.597 2.648l3.203-1.742M3 8V5.033c0-2.31 2.534-3.769 4.597-2.648l12.812 6.968a2.998 2.998 0 0 1 0 5.294l-6.406 3.484"/></svg>';
        }
    }

    playPauseBtn.addEventListener('click', togglePlayPause);
    centerPlayPauseBtn.addEventListener('click', togglePlayPause);

    forwardBtn.addEventListener('click', () => {
        video.currentTime = Math.min(video.duration, video.currentTime + 5);
    });

    // Backward 5 seconds
    backwardBtn.addEventListener('click', () => {
        video.currentTime = Math.max(0, video.currentTime - 5);
    });

    // Update seek bar as video plays
    video.addEventListener('timeupdate', () => {
        const value = (video.currentTime / video.duration) * 100;
        seekBar.value = value;
        seekBar.style.background = `linear-gradient(to right, black ${value}%, #ddd ${value}%)`;

        // Update current time display
        const currentMinutes = Math.floor(video.currentTime / 60);
        const currentSeconds = Math.floor(video.currentTime % 60);
        currentTimeDisplay.textContent = `${currentMinutes}:${currentSeconds < 10 ? '0' + currentSeconds : currentSeconds}`;
    });

    // Seek functionality
    seekBar.addEventListener('input', (event) => {
        video.currentTime = (event.target.value / 100) * video.duration;
    });

    // Mute/Unmute functionality
    muteBtn.addEventListener('click', () => {
        video.muted = !video.muted;
        muteBtn.innerHTML = video.muted ? '<svg xmlns="http://www.w3.org/2000/svg" width="20px" height="20px" viewBox="0 0 24 24"><path fill="currentColor" d="M11.553 3.064A.75.75 0 0 1 12 3.75v16.5a.75.75 0 0 1-1.255.555L5.46 16H2.75A1.75 1.75 0 0 1 1 14.25v-4.5C1 8.784 1.784 8 2.75 8h2.71l5.285-4.805a.75.75 0 0 1 .808-.13ZM10.5 5.445l-4.245 3.86a.75.75 0 0 1-.505.195h-3a.25.25 0 0 0-.25.25v4.5c0 .138.112.25.25.25h3c.187 0 .367.069.505.195l4.245 3.86Zm8.218-1.223a.75.75 0 0 1 1.06 0c4.296 4.296 4.296 11.26 0 15.556a.75.75 0 0 1-1.06-1.06a9.5 9.5 0 0 0 0-13.436a.75.75 0 0 1 0-1.06"/><path fill="currentColor" d="M16.243 7.757a.75.75 0 1 0-1.061 1.061a4.5 4.5 0 0 1 0 6.364a.75.75 0 0 0 1.06 1.06a6 6 0 0 0 0-8.485Z"/></svg>' : '<svg xmlns="http://www.w3.org/2000/svg" width="20px" height="20px" viewBox="0 0 24 24"><path fill="currentColor" d="M12 3.75v16.5a.75.75 0 0 1-1.255.555L5.46 16H2.75A1.75 1.75 0 0 1 1 14.25v-4.5C1 8.784 1.784 8 2.75 8h2.71l5.285-4.805A.75.75 0 0 1 12 3.75M6.255 9.305a.75.75 0 0 1-.505.195h-3a.25.25 0 0 0-.25.25v4.5c0 .138.112.25.25.25h3c.187 0 .367.069.505.195l4.245 3.86V5.445ZM16.28 8.22a.75.75 0 1 0-1.06 1.06L17.94 12l-2.72 2.72a.75.75 0 1 0 1.06 1.06L19 13.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L20.06 12l2.72-2.72a.75.75 0 0 0-1.06-1.06L19 10.94z"/></svg>';
    });

    // Show/Hide volume control
    volumeBtn.addEventListener('click', (event) => {
        event.stopPropagation();  // Prevent the event from bubbling up to the document
        volumeSlider.style.display = (volumeSlider.style.display === 'block') ? 'none' : 'block';
    });

    // Update volume
    volumeBar.addEventListener('input', () => {
        video.volume = volumeBar.value;
        const value = volumeBar.value * 100;
        volumeBar.style.background = `linear-gradient(to right, black ${value}%, #ddd ${value}%)`;
    });

    // Hide volume slider when clicking outside
    document.addEventListener('click', (event) => {
        if (!volumeSlider.contains(event.target) && event.target !== volumeBtn) {
            volumeSlider.style.display = 'none';
        }
    });
});
