document.addEventListener('DOMContentLoaded', function () {
    const uploadButton = document.getElementById('upload_new_material');
    const uploadModal = document.getElementById('uploadModal');
    const closeModal = document.getElementById('closeModal');
    const uploadForm = document.getElementById('uploadForm');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const deleteConfirmationModal = document.getElementById('deleteConfirmationModal');
    const closeDeleteModal = document.getElementById('closeDeleteModal');
    const cancelDeleteButton = document.getElementById('cancelDeleteButton');
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');
    let materialIdToDelete;
    const modalUploadButton = uploadModal.querySelector('#upload_material');

    uploadButton.addEventListener('click', function () {
        uploadModal.showModal();
    });

    closeModal.addEventListener('click', function () {
        uploadModal.close();
    });

    uploadForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const formData = new FormData(uploadForm);
        loadingIndicator.style.display = 'flex';
        modalUploadButton.disabled = true;

        fetch(uploadForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
            .then(response => response.json())
            .then(data => {
                loadingIndicator.style.display = 'none';
                modalUploadButton.disabled = false;
                if (data.success) {
                    alert('File uploaded and processed successfully!');
                    uploadModal.close();
                    location.reload(); // Optionally, refresh the page to reflect the new upload
                } else {
                    alert('There was an error processing your file. Please try again.');
                }
            })
            .catch(error => {
                loadingIndicator.style.display = 'none';
                modalUploadButton.disabled = false;
                alert('An error occurred. Please try again.');
            });
    });

    // Function to handle delete material
    function deleteMaterial(materialId) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const deleteUrl = `/delete_material/${materialId}/`;
        console.log(deleteUrl);

        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Material deleted successfully!');
                    location.reload(); // Optionally, refresh the page to reflect the deleted material
                } else {
                    alert('Error deleting material: ' + data.error);
                }
            })
            .catch(error => {
                alert('An error occurred while deleting the material. Please try again.');
            });
    }


    // Event listener for delete buttons
    document.querySelectorAll('.delete_study_material_button').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            materialIdToDelete = this.getAttribute('data-id');
            console.log("Material ID to delete:", materialIdToDelete);  // Log the ID
            deleteConfirmationModal.showModal();
        });
    });

    closeDeleteModal.addEventListener('click', function () {
        console.log("Close delete modal clicked");  // Log close button
        deleteConfirmationModal.close();
    });

    cancelDeleteButton.addEventListener('click', function () {
        console.log("Cancel delete button clicked");  // Log cancel button
        deleteConfirmationModal.close();
    });

    confirmDeleteButton.addEventListener('click', function () {
        console.log("Confirm delete button clicked");  // Log confirm button
        if (materialIdToDelete) {
            deleteMaterial(materialIdToDelete);
            deleteConfirmationModal.close();
        }
    });
});
