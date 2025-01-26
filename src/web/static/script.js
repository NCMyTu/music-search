function handleUpload(buttonClass) {
    const uploadButton = document.querySelector(`.${buttonClass}`);

    uploadButton.addEventListener('click', () => {
        // create an invisible file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = ".mp3";
        fileInput.style.display = 'none';

        document.body.appendChild(fileInput);

        fileInput.click();

        fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);

                fetch('/upload', {
                    method: 'POST',
                    body: formData  
                })
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    updateSongDetails(data["songname"], data["artists"])
                })
                .catch(error => {
                    console.error('Error uploading file:', error);
                    alert('Error uploading file.');
                });
            }

            // remove the temporary file input
            document.body.removeChild(fileInput);
        });
    });
}

function handleRecord(buttonClass) {
    const recordButton = document.querySelector(`.${buttonClass}`);
    let mediaRecorder;
    let chunks = [];
    let mediaStream;

    recordButton.addEventListener('click', async () => {
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            try {
                // request permission for audio recording
                mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

                mediaRecorder = new MediaRecorder(mediaStream);

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        chunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = async () => {
                    // create the audio file from the recorded chunks
                    const blob = new Blob(chunks, { type: 'audio/mpeg' });
                    chunks = [];

                    // release the microphone
                    mediaStream.getTracks().forEach(track => track.stop());

                    const formData = new FormData();
                    formData.append('file', blob, 'query.mp3');

                    fetch('/upload', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log(data);
                        updateSongDetails(data["songname"], data["artists"])
                    })
                    .catch(error => {
                        console.error('Error uploading file:', error);
                        alert('Error uploading file.');
                    });
                };

                mediaRecorder.start();
                recordButton.textContent = 'Stop Recording';
            } catch (error) {
                console.error('Error accessing microphone:', error);
                alert('Could not access microphone.');
            }
        } else if (mediaRecorder && mediaRecorder.state === 'recording') {
            // stop the recording
            mediaRecorder.stop();
            recordButton.textContent = 'Record';
        }
    });
}

function updateSongDetails(songName, artists) {
    const resultCenter = document.querySelector('center');
    const songNameElement = document.querySelector('.song-name');
    const artistsElement = document.querySelector('.artists');
    
    songNameElement.textContent = `Song name: ${songName}`;
    artistsElement.textContent = `Artists: ${artists}`;

    resultCenter.style.visibility = 'visible';
}

handleUpload('play-btn');
handleRecord('follow-btn');