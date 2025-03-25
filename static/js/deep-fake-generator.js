document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const resultSection = document.querySelector('.result-section');
    const sourceImage = document.querySelector('.result-section .result-card:nth-child(1) img');
    const targetImage = document.querySelector('.result-section .result-card:nth-child(2) img');
    const resultImage = document.querySelector('.result-section .result-card:nth-child(3) img');
    const downloadBtn = document.createElement('a');
    downloadBtn.className = 'btn';
    downloadBtn.textContent = 'Download Result';
    downloadBtn.style.marginTop = '20px';

    let outputFilename = null;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Create loading indicator
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        const formData = new FormData(form);

        try {
            const response = await fetch('/gen-deepfake', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Show result section
                resultSection.style.display = 'block';

                // Update images
                sourceImage.src = URL.createObjectURL(formData.get('source_image'));
                targetImage.src = URL.createObjectURL(formData.get('target_image'));
                resultImage.src = `/static/processed/${data.output_filename}`;

                // Store output filename for later deletion
                outputFilename = data.output_filename;

                // Add download button to the result section
                downloadBtn.href = `/download-deepfake/${outputFilename}`;
                if (!document.querySelector('.result-container').contains(downloadBtn)) {
                    document.querySelector('.result-container').appendChild(downloadBtn);
                }

                // Scroll to results
                resultSection.scrollIntoView({ behavior: 'smooth' });

                // Reset form
                form.reset();
            } else {
                alert(`Error: ${data.message}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during processing. Please try again.');
        } finally {
            // Reset button
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    });

    // Delete the output file after download
    downloadBtn.addEventListener('click', async function() {
        if (outputFilename) {
            // Wait a bit to ensure download starts before deleting
            setTimeout(async () => {
                try {
                    await fetch(`/delete-output/${outputFilename}`, {
                        method: 'POST'
                    });
                    console.log('Output file deleted successfully');
                } catch (error) {
                    console.error('Error deleting output file:', error);
                }
            }, 3000);
        }
    });
});