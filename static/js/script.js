document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const preview = document.getElementById('preview');
    const removeBackgroundBtn = document.getElementById('removeBackground');
    const optionsSection = document.querySelector('.options-section');
    const resultSection = document.querySelector('.result-section');
    const resultImage = document.getElementById('resultImage');
    const colorPicker = document.getElementById('colorPicker');
    const bgFileInput = document.getElementById('bgFileInput');
    const downloadPNG = document.getElementById('downloadPNG');
    const downloadJPG = document.getElementById('downloadJPG');
    const loader = document.querySelector('.loader');
    let processedImage = null;

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        handleFile(file);
    }

    function handleFile(file) {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.hidden = false;
                document.querySelector('.upload-content').hidden = true;
                optionsSection.hidden = false;
            };
            reader.readAsDataURL(file);
        }
    }

    // Remove background functionality
    removeBackgroundBtn.addEventListener('click', async () => {
        if (!preview.src) return;

        showLoader();

        try {
            const formData = new FormData();
            const blob = await fetch(preview.src).then(r => r.blob());
            formData.append('image', blob);

            const response = await fetch('/remove-background', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.status === 'success') {
                processedImage = data.image;
                resultImage.src = processedImage;
                resultSection.hidden = false;
            } else {
                throw new Error(data.error || 'Failed to process image');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error processing image: ' + error.message);
        } finally {
            hideLoader();
        }
    });

    // Background color and image functionality
    colorPicker.addEventListener('input', () => {
        if (!processedImage) return;
        applyBackground('color', colorPicker.value);
    });

    bgFileInput.addEventListener('change', (e) => {
        if (!processedImage || !e.target.files[0]) return;
        
        const file = e.target.files[0];
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            applyBackground('image', e.target.result);
        };
        reader.readAsDataURL(file);
    });

    async function applyBackground(type, value, format = 'PNG') {
        showLoader();

        try {
            const response = await fetch('/apply-background', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: processedImage,
                    backgroundType: type,
                    backgroundValue: value,
                    format: format
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.status === 'success') {
                resultImage.src = data.image;
            } else {
                throw new Error(data.error || 'Failed to apply background');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error applying background: ' + error.message);
        } finally {
            hideLoader();
        }
    }

    // Download functionality
    downloadPNG.addEventListener('click', () => {
        if (resultImage.src) {
            downloadImage(resultImage.src, 'bg-removed.png');
        }
    });

    downloadJPG.addEventListener('click', async () => {
        if (resultImage.src && processedImage) {
            showLoader();
            try {
                const response = await fetch('/apply-background', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        image: processedImage,
                        backgroundType: 'color',
                        backgroundValue: colorPicker.value,
                        format: 'JPEG'
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                if (data.status === 'success') {
                    downloadImage(data.image, 'bg-removed.jpg');
                } else {
                    throw new Error(data.error || 'Failed to convert to JPEG');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error downloading JPEG: ' + error.message);
            } finally {
                hideLoader();
            }
        }
    });

    function downloadImage(dataUrl, filename) {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function showLoader() {
        loader.hidden = false;
    }

    function hideLoader() {
        loader.hidden = true;
    }
});
