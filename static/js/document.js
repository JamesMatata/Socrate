document.addEventListener('DOMContentLoaded', function () {
    const materialDataElement = document.getElementById('materialData');
    if (!materialDataElement) {
        console.error("Material data element not found");
        return;
    }

    let material;
    try {
        material = JSON.parse(materialDataElement.textContent);
        console.log("Parsed material data:", material);
    } catch (e) {
        console.error("Error parsing material data:", e);
        return;
    }

    const fileUrl = material.file_url;
    const fileType = material.material_type;
    const output = document.getElementById('output');
    const fileInfo = document.getElementById('fileInfo');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('errorMsg');
    const pageControls = document.getElementById('pageControls');
    const zoomControls = document.getElementById('zoomControls');
    let pdfDoc = null;
    let currentPage = 1;
    let totalPages = 1;
    let currentScale = 1.0;
    let isDocx = false;

    console.log("File URL:", fileUrl);
    console.log("File Type:", fileType);

    function applyZoom() {
        const docxContainer = document.querySelector('.docx-container');
        if (docxContainer) {
            docxContainer.style.width = `${currentScale * 100}%`;
            docxContainer.style.fontSize = `${currentScale * 16}px`;
        } else {
            renderPage(currentPage);
        }
    }

    function displayText(content) {
        output.textContent = content;
    }

    function displayPDF(content) {
        const pdfData = new Uint8Array(content);
        const loadingTask = pdfjsLib.getDocument({ data: pdfData });

        loadingTask.promise.then(function (pdf) {
            pdfDoc = pdf;
            totalPages = pdf.numPages;
            document.getElementById('totalPages').textContent = totalPages;
            pageControls.style.display = 'block';
            zoomControls.style.display = 'block';
            renderPage(currentPage);
        }, function (reason) {
            console.error("Error loading PDF:", reason);
            errorMsg.textContent = 'Failed to load PDF.';
        });
    }

    function renderPage(pageNumber) {
        if (pdfDoc) {
            pdfDoc.getPage(pageNumber).then(function (page) {
                const viewport = page.getViewport({ scale: currentScale });

                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                const renderContext = {
                    canvasContext: context,
                    viewport: viewport
                };
                page.render(renderContext).promise.then(function () {
                    output.innerHTML = '';
                    output.appendChild(canvas);
                    document.getElementById('currentPage').textContent = currentPage;
                });
            }).catch(function (error) {
                console.error("Error rendering page:", error);
                errorMsg.textContent = 'Failed to render page.';
            });
        }
    }

    function displayDOCX(content) {
        mammoth.convertToHtml({ arrayBuffer: content })
            .then(function (result) {
                output.innerHTML = `<div class="docx-container" style="font-size: ${currentScale * 16}px;">${result.value}</div>`;
                currentScale = 1.0;
                isDocx = true;
                zoomControls.style.display = 'block';
                document.getElementById('currentPage').textContent = 1;
                document.getElementById('totalPages').textContent = 1;
            })
            .catch(function (err) {
                console.error("Error loading DOCX:", err);
                errorMsg.textContent = 'Failed to load DOCX.';
            });
    }

    function fetchAndDisplayFile() {
        loading.style.display = 'block';
        console.log("Fetching file from URL:", fileUrl);

        fetch(fileUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load file: ${response.statusText}`);
                }
                return response.arrayBuffer();
            })
            .then(content => {
                loading.style.display = 'none';
                console.log("File fetched successfully");

                if (fileType === 'pdf') {
                    displayPDF(content);
                } else if (fileType === 'word') {
                    displayDOCX(content);
                } else {
                    displayText(new TextDecoder().decode(content));
                }
            })
            .catch(error => {
                loading.style.display = 'none';
                console.error("Error fetching file:", error);
                errorMsg.textContent = error.message;
            });
    }

    document.getElementById('prevPageBtn').addEventListener('click', function () {
        if (currentPage <= 1) return;
        currentPage--;
        renderPage(currentPage);
    });

    document.getElementById('nextPageBtn').addEventListener('click', function () {
        if (currentPage >= totalPages) return;
        currentPage++;
        renderPage(currentPage);
    });

    document.getElementById('zoomInBtn').addEventListener('click', function () {
        currentScale += 0.1;
        applyZoom();
    });

    document.getElementById('zoomOutBtn').addEventListener('click', function () {
        if (currentScale > 0.5) {
            currentScale -= 0.1;
            applyZoom();
        }
    });

    fetchAndDisplayFile();
});
