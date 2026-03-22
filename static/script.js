const dropArea = document.getElementById('drop-area');
const fileElem = document.getElementById('fileElem');
const processBtn = document.getElementById('processBtn');
const statusContainer = document.getElementById('status-container');
const resultContainer = document.getElementById('result-container');
const statusTitle = document.getElementById('status-title');
const statusMessage = document.getElementById('status-message');
const downloadBtn = document.getElementById('downloadBtn');
const directionSelect = document.getElementById('direction');
const spinner = document.getElementById('spinner');

let selectedFile = null;
let currentMode = 'dub';

document.getElementById('tab-dub').addEventListener('click', () => {
    currentMode = 'dub';
    document.getElementById('tab-dub').classList.add('active');
    document.getElementById('tab-clip').classList.remove('active');
    document.getElementById('tab-watermark').classList.remove('active');
    document.getElementById('dub-controls').classList.remove('hidden');
    document.getElementById('clip-controls').classList.add('hidden');
    document.getElementById('watermark-controls').classList.add('hidden');
});

document.getElementById('tab-clip').addEventListener('click', () => {
    currentMode = 'clip';
    document.getElementById('tab-clip').classList.add('active');
    document.getElementById('tab-dub').classList.remove('active');
    document.getElementById('tab-watermark').classList.remove('active');
    document.getElementById('clip-controls').classList.remove('hidden');
    document.getElementById('dub-controls').classList.add('hidden');
    document.getElementById('watermark-controls').classList.add('hidden');
});

document.getElementById('tab-watermark').addEventListener('click', () => {
    currentMode = 'watermark';
    document.getElementById('tab-watermark').classList.add('active');
    document.getElementById('tab-dub').classList.remove('active');
    document.getElementById('tab-clip').classList.remove('active');
    document.getElementById('watermark-controls').classList.remove('hidden');
    document.getElementById('dub-controls').classList.add('hidden');
    document.getElementById('clip-controls').classList.add('hidden');
});

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false);
  document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults (e) {
  e.preventDefault();
  e.stopPropagation();
}

// Highlight drop area when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
  dropArea.classList.add('highlight');
}

function unhighlight(e) {
  dropArea.classList.remove('highlight');
}

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  handleFiles(files);
}

dropArea.addEventListener('click', () => {
    fileElem.click();
});

fileElem.addEventListener('change', function() {
    handleFiles(this.files);
});

function handleFiles(files) {
    if (files.length > 0) {
        selectedFile = files[0];
        dropArea.querySelector('p').textContent = selectedFile.name;
        dropArea.querySelector('h3').textContent = 'Video seleccionado';
        processBtn.disabled = false;
        
        // Reset state
        statusContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        spinner.style.display = 'block';
        statusTitle.textContent = "Traduciendo...";
        statusTitle.style.color = "var(--text-main)";
    }
}

processBtn.addEventListener('click', () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('direction', directionSelect.value);
    formData.append('mode', currentMode);

    // Update UI
    dropArea.style.pointerEvents = 'none';
    processBtn.disabled = true;
    directionSelect.disabled = true;
    statusContainer.classList.remove('hidden');

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            handleError(data.error);
        } else {
            pollStatus(data.job_id);
        }
    })
    .catch(error => {
        handleError("Error de conexión con el servidor.");
    });
});

function pollStatus(jobId) {
    const interval = setInterval(() => {
        fetch(`/status/${jobId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                clearInterval(interval);
                handleError(data.error);
                return;
            }

            statusMessage.textContent = data.message;

            if (data.status === 'done') {
                clearInterval(interval);
                statusContainer.classList.add('hidden');
                resultContainer.classList.remove('hidden');
                
                if (currentMode === 'dub') {
                    downloadBtn.href = `/download/${jobId}`;
                    downloadBtn.download = `traducido_${selectedFile.name}`;
                    downloadBtn.style.display = 'inline-flex';
                    document.getElementById('clips-list').innerHTML = '';
                } else if (currentMode === 'watermark') {
                    downloadBtn.href = `/download/${jobId}`;
                    downloadBtn.download = `limpio_${selectedFile.name}`;
                    downloadBtn.style.display = 'inline-flex';
                    document.getElementById('clips-list').innerHTML = '';
                } else {
                    downloadBtn.style.display = 'none';
                    let clipsHtml = "<h5 style='color: var(--text-muted); margin-bottom: 10px;'>Clips Generados (9:16):</h5><div class='clips-grid'>";
                    data.clips.forEach(clipname => {
                        clipsHtml += `<a class="download-button" style="margin:5px; padding: 10px; font-size: 0.9em;" href="/download_clip/${jobId}/${clipname}" download>Descargar ${clipname}</a>`;
                    });
                    clipsHtml += "</div>";
                    document.getElementById('clips-list').innerHTML = clipsHtml;
                }
                
                // Allow new submissions
                dropArea.style.pointerEvents = 'auto';
                directionSelect.disabled = false;
                processBtn.disabled = false;
                dropArea.querySelector('p').textContent = 'Arrastra otro video o haz clic';
            } else if (data.status === 'error') {
                clearInterval(interval);
                handleError(data.message);
            }
        })
        .catch(() => {
            // Keep polling even if one request fails
        });
    }, 5000); // Check every 5 seconds since translation takes minutes
}

function handleError(msg) {
    statusTitle.textContent = "Hubo un error";
    statusTitle.style.color = "#ef4444";
    statusMessage.textContent = msg;
    spinner.style.display = 'none';
    
    // Allow trying again
    dropArea.style.pointerEvents = 'auto';
    directionSelect.disabled = false;
    processBtn.disabled = false;
}
