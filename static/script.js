const fileInput = document.getElementById("fileInput");
const previewBox = document.getElementById("previewBox");
const cameraBtn = document.getElementById("cameraBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const nutritionBox = document.getElementById("nutritionBox");
const nutritionContent = document.getElementById("nutritionContent");

// Image preview (before clicking the analyze button)
fileInput?.addEventListener("change", function () {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      previewBox.innerHTML = `<img src="${e.target.result}" class="preview-img">`;
    };
    reader.readAsDataURL(file);
  }
});

// Camera button (open webcam and capture)
cameraBtn?.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    const video = document.createElement("video");
    video.autoplay = true;
    video.playsInline = true;
    video.style.width = "100%";
    video.style.height = "100%";
    previewBox.innerHTML = "";
    previewBox.appendChild(video);
    video.srcObject = stream;

    setTimeout(() => {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0);
      stream.getTracks().forEach((t) => t.stop());

      canvas.toBlob((blob) => {
        const file = new File([blob], "camera.jpg", { type: "image/jpeg" });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        const reader = new FileReader();
        reader.onload = (e) => {
          previewBox.innerHTML = `<img src="${e.target.result}" class="preview-img">`;
        };
        reader.readAsDataURL(file);
      });
    }, 3000);
  } catch (err) {
    alert("Camera access denied or unavailable.");
    console.error(err);
  }
});

// Analyze button
analyzeBtn?.addEventListener("click", async (e) => {
  e.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    alert("Please upload or take a photo first!");
    return;
  }

  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch("/predict", { method: "POST", body: formData });
  const data = await response.json();

  if (data.error) {
    alert(data.error);
    return;
  }

  if (data.result_image) {
    const url = data.result_image.startsWith("/")
      ? data.result_image
      : `/${data.result_image.replace(/\\/g, "/")}`;
    previewBox.innerHTML = `<img src="${url}?t=${Date.now()}" class="preview-img">`;
  }

  nutritionContent.innerHTML = "";
  nutritionBox.querySelector(".nutrition-total")?.remove();
  const totals = {};
  let hasValidItems = false;
  let html = "";

  nutritionBox.classList.remove("hidden");
  setTimeout(() => nutritionBox.classList.add("show"), 50);

  if (Array.isArray(data.items)) {
    data.items.forEach((item) => {
      if (!item.name || !item.nutrition) return;
      hasValidItems = true;
      let nutritionList = "";

      for (const [key, value] of Object.entries(item.nutrition)) {
        const match = value.toString().match(/^([\d.]+)\s*(.*)$/);
        if (!match) continue;
        const num = parseFloat(match[1]);
        const unit = match[2] || "";
        const multiplied = Math.round(num * item.count * 1000) / 1000;
        nutritionList += `<li>${key}: ${multiplied}${unit}</li>`;

        if (!isNaN(num)) {
          if (!totals[key]) totals[key] = { value: 0, unit };
          totals[key].value += multiplied;
        }
      }

      if (nutritionList)
        html += `
        <div class="nutrition-item">
          <strong>${item.count} ${item.name}(s)</strong>
          <ul>${nutritionList}</ul>
        </div>
      `;
    });
  }

  if (hasValidItems) {
    nutritionContent.innerHTML = html;

    if (Object.keys(totals).length > 0) {
      const totalBox = document.createElement("div");
      totalBox.classList.add("nutrition-total");
      let totalHTML = `<h3>Total Nutritional Values</h3><ul>`;
      for (const [key, obj] of Object.entries(totals)) {
        const rounded = Math.round(obj.value * 1000) / 1000;
        totalHTML += `<li><strong>${key}</strong>: ${rounded}${obj.unit}</li>`;
      }
      totalHTML += `</ul>`;
      totalBox.innerHTML = totalHTML;
      nutritionBox.appendChild(totalBox);
    }
  } else {
    nutritionContent.innerHTML = `<p style="text-align:center; color:#666; font-style:italic;">No food detected</p>`;
  }

  const scoreBox = document.getElementById("nutritionScoreBox");
  const allergyBox = document.getElementById("allergyBox");
  const recommendationBox = document.getElementById("recommendationBox");

  if (data.nutrition_score && scoreBox) {
    scoreBox.innerHTML = `
      <div class="score-box">
        Nutrition Score: <strong>${data.nutrition_score.score}</strong>
        (${data.nutrition_score.label})<br>
        Calories: ${data.nutrition_coverage["Calories (%)"]}% |
        Protein: ${data.nutrition_coverage["Protein (%)"]}%<br>
        Vitamins: ${data.micronutrient_coverage["Vitamins (%)"]}% |
        Minerals: ${data.micronutrient_coverage["Minerals (%)"]}%
      </div>
    `;
  }

  if (data.allergy_information && allergyBox) {
    allergyBox.innerHTML = `
      <div class="warning-box">
        <strong>Allergy Information</strong>
        <ul>${data.allergy_information.map(a => `<li>${a}</li>`).join("")}</ul>
      </div>
    `;
  }

  if (data.recommendations && recommendationBox) {
    recommendationBox.innerHTML = `
      <div class="recommend-box">
        <strong>Recommendations</strong>
        <ul>${data.recommendations.map(r => `<li>${r}</li>`).join("")}</ul>
      </div>
    `;
  }
});
