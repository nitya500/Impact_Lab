/**
 * IMPACT LAB - Main Client JavaScript
 * INNOTECH'26 Innovation Initiative
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. Mobile Menu Navigation Toggle
    const mobileToggle = document.getElementById("mobileMenuToggle");
    const navMenu = document.getElementById("navMenu");

    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener("click", function () {
            navMenu.classList.toggle("open");
        });
    }

    // 2. Client-side Validation for Problem Submission Form
    const problemForm = document.getElementById("problemSubmitForm");
    if (problemForm) {
        problemForm.addEventListener("submit", function (e) {
            let isValid = true;
            const titleInput = document.getElementById("problemTitle");
            const descInput = document.getElementById("problemDescription");
            const categoryInput = document.getElementById("category");

            // Title validation
            if (!titleInput.value.trim() || titleInput.value.trim().length < 5) {
                isValid = false;
                titleInput.classList.add("is-invalid");
                const feedback = document.getElementById("titleFeedback");
                if (feedback) feedback.style.display = "block";
            } else {
                titleInput.classList.remove("is-invalid");
                const feedback = document.getElementById("titleFeedback");
                if (feedback) feedback.style.display = "none";
            }

            // Description validation
            if (!descInput.value.trim() || descInput.value.trim().length < 20) {
                isValid = false;
                descInput.classList.add("is-invalid");
            } else {
                descInput.classList.remove("is-invalid");
            }

            // Category validation
            if (!categoryInput.value) {
                isValid = false;
                categoryInput.classList.add("is-invalid");
            } else {
                categoryInput.classList.remove("is-invalid");
            }

            if (!isValid) {
                e.preventDefault();
                showToast("Please fill in all required fields accurately before submitting.", "error");
            } else {
                const submitBtn = document.getElementById("submitBtn");
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = "Posting Problem...";
                }
            }
        });
    }

    // 3. Auto-dismiss alerts after 5 seconds
    const flashAlerts = document.querySelectorAll(".alert");
    flashAlerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "opacity 0.4s ease";
            alert.style.opacity = "0";
            setTimeout(function () {
                alert.remove();
            }, 400);
        }, 5000);
    });
});

/**
 * Toast Notification Helper
 */
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `alert alert-${type}`;
    toast.style.cssText = "box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 0.5rem;";
    toast.innerHTML = `<span>${message}</span><button type="button" class="close-alert" onclick="this.parentElement.remove();">&times;</button>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = "opacity 0.4s ease";
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 400);
    }, 4500);
}

/**
 * Backward compatibility functions for legacy API calls (if invoked)
 */
async function sendData(url, data) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.error || "Request failed.");
    }
    return result;
}

async function getData(url) {
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) {
        throw new Error("Could not load data.");
    }
    return data;
}