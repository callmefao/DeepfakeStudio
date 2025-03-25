// Video processing utility functions
const VideoHandler = {
  // Initialize the video player for uploaded files
  initUploadedVideo: (videoUrl) => {
    const videoStream = document.getElementById("video-stream")
    if (videoStream) {
      // Update the image source to the processed video feed URL
      videoStream.src = videoUrl + "?" + new Date().getTime()

      // Show success message
      const uploadStatus = document.getElementById("upload-status")
      if (uploadStatus) {
        uploadStatus.textContent = "Video processing started"
        uploadStatus.className = "status-message success"
      }
    }
  },

  // Handle upload form submission
  setupUploadForm: () => {
    const uploadForm = document.getElementById("upload-form")
    const uploadSubmitBtn = document.getElementById("upload-submit-btn")
    const uploadStatus = document.getElementById("upload-status")
    const loadingSpinner = document.getElementById("loading-spinner")

    if (!uploadForm) return

    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const mediaFile = document.getElementById("media_file").files[0]
      if (!mediaFile) {
        uploadStatus.textContent = "Please select a file to upload"
        uploadStatus.className = "status-message error"
        return
      }

      // Disable button and show loading state
      uploadSubmitBtn.disabled = true
      uploadSubmitBtn.classList.add("loading")

      // Show loading spinner
      loadingSpinner.querySelector(".spinner-text").textContent = "Uploading and processing file..."
      loadingSpinner.classList.add("active")

      try {
        const formData = new FormData(uploadForm)
        const response = await fetch("/detect-deepfake/upload", {
          method: "POST",
          body: formData,
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            // Initialize video with the processed URL
            VideoHandler.initUploadedVideo(data.video_url)
          } else {
            uploadStatus.textContent = data.message || "Failed to process file"
            uploadStatus.className = "status-message error"
          }
        } else {
          uploadStatus.textContent = "Server error. Please try again."
          uploadStatus.className = "status-message error"
        }
      } catch (error) {
        console.error("Error:", error)
        uploadStatus.textContent = "An error occurred. Please try again."
        uploadStatus.className = "status-message error"
      } finally {
        uploadSubmitBtn.disabled = false
        uploadSubmitBtn.classList.remove("loading")
        loadingSpinner.classList.remove("active")
      }
    })
  },
}

// Initialize when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  VideoHandler.setupUploadForm()
})

