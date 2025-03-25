document.addEventListener("DOMContentLoaded", () => {
  // Get references to DOM elements
  const uploadForm = document.getElementById("upload-form")
  const uploadSubmitBtn = document.getElementById("upload-submit-btn")
  const uploadStatus = document.getElementById("upload-status")
  const loadingSpinner = document.getElementById("loading-spinner")

  // Function to show loading spinner
  function showSpinner(message = "Loading...") {
    loadingSpinner.querySelector(".spinner-text").textContent = message
    loadingSpinner.classList.add("active")
  }

  // Function to hide loading spinner
  function hideSpinner() {
    loadingSpinner.classList.remove("active")
  }

  // Function to show status message
  function showStatus(element, message, type) {
    element.textContent = message
    element.className = "status-message " + type
    setTimeout(() => {
      element.className = "status-message"
    }, 5000)
  }

  // Handle upload form submission
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const mediaFile = document.getElementById("media_file").files[0]
      if (!mediaFile) {
        showStatus(uploadStatus, "Please select a file to upload", "error")
        return
      }

      // Check if file is a video
      const allowedTypes = ["video/mp4", "video/avi", "video/quicktime", "video/x-matroska", "video/webm"]
      if (!allowedTypes.includes(mediaFile.type)) {
        showStatus(uploadStatus, "Please upload a video file", "error")
        return
      }

      // Disable button and show loading state
      uploadSubmitBtn.disabled = true
      uploadSubmitBtn.classList.add("loading")
      showSpinner("Uploading and processing video...")

      try {
        const formData = new FormData(uploadForm)
        const response = await fetch("/detect-deepfake/upload", {
          method: "POST",
          body: formData,
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            // Redirect to the view page for the processed video
            window.location.href = data.view_url
          } else {
            showStatus(uploadStatus, data.message || "Failed to process video", "error")
            uploadSubmitBtn.disabled = false
            uploadSubmitBtn.classList.remove("loading")
            hideSpinner()
          }
        } else {
          showStatus(uploadStatus, "Server error. Please try again.", "error")
          uploadSubmitBtn.disabled = false
          uploadSubmitBtn.classList.remove("loading")
          hideSpinner()
        }
      } catch (error) {
        console.error("Error:", error)
        showStatus(uploadStatus, "An error occurred. Please try again.", "error")
        uploadSubmitBtn.disabled = false
        uploadSubmitBtn.classList.remove("loading")
        hideSpinner()
      }
    })
  }
})

