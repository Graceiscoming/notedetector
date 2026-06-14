document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name');
    const processBtn = document.getElementById('process-btn');
    const stemSelect = document.getElementById('stem-select');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    
    let selectedFile = null;

    // Drag and Drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('audio/')) {
            alert('Please select an audio file (MP3, WAV, etc.)');
            return;
        }
        selectedFile = file;
        fileNameDisplay.textContent = `Selected: ${file.name}`;
        processBtn.disabled = false;
        resultsDiv.classList.add('hidden');
    }

    processBtn.addEventListener('click', async () => {
        const songNameInput = document.getElementById('song-name').value.trim();
        if (!songNameInput) {
            alert('Please enter a Song Name to create a project folder.');
            return;
        }
        if (!selectedFile) return;

        // UI State
        processBtn.disabled = true;
        uploadArea.style.pointerEvents = 'none';
        uploadArea.style.opacity = '0.5';
        loadingDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('stem', stemSelect.value);
        formData.append('song_name', songNameInput);

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Processing failed');
            }

            const data = await response.json();
            
            // Show Results
            document.getElementById('download-midi').href = data.midi_url;
            document.getElementById('download-text').href = data.text_url;
            
            loadingDiv.classList.add('hidden');
            resultsDiv.classList.remove('hidden');

        } catch (error) {
            alert(`Error: ${error.message}`);
            loadingDiv.classList.add('hidden');
        } finally {
            processBtn.disabled = false;
            uploadArea.style.pointerEvents = 'auto';
            uploadArea.style.opacity = '1';
        }
    });
});
