document.addEventListener("DOMContentLoaded", function () {
    const summarizeTextButton = document.getElementById("summarize-text-button");
    const summarizeFileButton = document.getElementById("summarize-file-button");
    const inputText = document.getElementById("input-text");
    const textSummaryOutput = document.getElementById("text-summary-output");
    const fileInput = document.getElementById("file-input");
    const fileSummaryOutput = document.getElementById("file-summary-output");

    // Handle Text Summarization
    if (summarizeTextButton && inputText && textSummaryOutput) {
        summarizeTextButton.addEventListener("click", async function () {
            try {
                const text = inputText.value.trim();
                if (!text) throw new Error("Please enter some text to summarize.");

                textSummaryOutput.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Generating summary...</div>';
                const response = await fetch("/api/summarize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: text }),
                });

                if (!response.ok) throw new Error("Error generating summary.");
                const data = await response.json();

                textSummaryOutput.innerHTML = `
                    <h4>Summary:</h4>
                    <p>${data.summary}</p>
                `;
            } catch (error) {
                textSummaryOutput.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
            }
        });
    }

    // Handle File Summarization
    if (summarizeFileButton && fileInput && fileSummaryOutput) {
        summarizeFileButton.addEventListener("click", async function () {
            try {
                const file = fileInput.files[0];
                if (!file) throw new Error("Please upload a file to summarize.");

                const formData = new FormData();
                formData.append("file", file);

                fileSummaryOutput.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Generating summary...</div>';
                const response = await fetch("/api/summarize-file", {
                    method: "POST",
                    body: formData,
                });

                if (!response.ok) throw new Error("Error generating summary.");
                const data = await response.json();

                fileSummaryOutput.innerHTML = `
                    <h4>Summary:</h4>
                    <p>${data.summary}</p>
                `;
            } catch (error) {
                fileSummaryOutput.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
            }
        });
    }
});
