// By default, the API runs alongside this page. For a separate deployed frontend,
// set window.SMARTCROP_API_URL to the deployed API origin before this script loads.
const API_BASE_URL = (window.SMARTCROP_API_URL || window.location.origin).replace(/\/$/, "");
document.getElementById("apiDocsLink").href = `${API_BASE_URL}/docs`;

const form = document.getElementById("predictionForm");
const result = document.getElementById("result");
const limeResults = document.getElementById("limeResults");
const loading = document.getElementById("loadingDiv");
const predictButton = document.getElementById("predictBtn");
const explainButton = document.getElementById("explainBtn");

function getFormData() {
  return {
    N: Number(document.getElementById("N").value),
    P: Number(document.getElementById("P").value),
    K: Number(document.getElementById("K").value),
    temperature: Number(document.getElementById("temperature").value),
    rainfall: Number(document.getElementById("rainfall").value),
    ph: Number(document.getElementById("ph").value),
    Humidity_calculated: Number(document.getElementById("humidity").value),
    State_Name: document.getElementById("State_Name").value,
    Crop_Type: document.getElementById("Crop_Type").value,
    Area_in_hectares: Number(document.getElementById("area").value),
    Production_in_tons: Number(document.getElementById("production").value),
    Yield_ton_per_hec: Number(document.getElementById("yield").value),
  };
}

function setLoading(isLoading, message = "Reading your field details…") {
  loading.classList.toggle("show", isLoading);
  loading.querySelector("span:last-child").textContent = message;
  predictButton.disabled = isLoading;
  explainButton.disabled = isLoading;
}

function showError(message) {
  result.innerHTML = "";
  const card = document.createElement("div");
  card.className = "error";
  card.setAttribute("role", "alert");
  card.textContent = message;
  result.append(card);
}

async function request(endpoint, data) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  } catch {
    throw new Error(`We couldn’t reach the crop service. Check that the API is running at ${API_BASE_URL}, then try again.`);
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : "Please check your field details and try again.";
    throw new Error(detail);
  }
  return payload;
}

function showPrediction(prediction) {
  if (!prediction.predicted_crop) throw new Error("The crop service did not return a recommendation. Please try again.");
  const confidence = Math.max(0, Math.min(100, Number(prediction.confidence) * 100));
  result.innerHTML = `
    <div class="success">
      <span class="recommendation-label">Our recommendation</span>
      <h2 class="crop-name"></h2>
      <div class="confidence-row"><span>Model confidence</span><strong>${confidence.toFixed(1)}%</strong></div>
      <div class="confidence-track" aria-label="Model confidence ${confidence.toFixed(1)} percent"><div class="confidence-fill" style="width:${confidence}%"></div></div>
      <p class="result-context">An estimate based on the information you provided. Consider it alongside local expertise.</p>
    </div>`;
  result.querySelector(".crop-name").textContent = prediction.predicted_crop;
}

function showExplanation(data) {
  if (data.status === "error") throw new Error(data.error_message || "We couldn’t prepare an explanation. Please try again.");
  const visualization = data.visualization?.image_base64;
  const advice = Array.isArray(data.top_advice) ? data.top_advice : [];
  limeResults.replaceChildren();

  const card = document.createElement("section");
  card.className = "lime-results";
  card.setAttribute("aria-label", "Recommendation explanation");
  const title = document.createElement("h2");
  title.textContent = `What shaped the ${data.predicted_crop || "crop"} recommendation`;
  card.append(title);

  if (visualization) {
    const figure = document.createElement("div");
    figure.className = "lime-image";
    const image = document.createElement("img");
    image.alt = `Feature impact chart for the ${data.predicted_crop || "predicted"} crop recommendation`;
    image.src = `data:image/png;base64,${visualization}`;
    figure.append(image);
    card.append(figure);
  }

  if (advice.length) {
    const adviceSection = document.createElement("div");
    adviceSection.className = "advice-section";
    const adviceTitle = document.createElement("div");
    adviceTitle.className = "advice-title";
    adviceTitle.textContent = "Field notes to consider";
    adviceSection.append(adviceTitle);
    advice.slice(0, 5).forEach((note) => {
      const item = document.createElement("div");
      item.className = "advice-item";
      item.textContent = note;
      adviceSection.append(item);
    });
    card.append(adviceSection);
  }

  if (data.summary) {
    const summary = document.createElement("div");
    summary.className = "result-card";
    const heading = document.createElement("h3");
    heading.textContent = "Explanation summary";
    summary.append(heading);
    const rows = [
      ["Features explored", data.summary.total_features_analyzed],
      ["Supporting factors", data.summary.positive_impact_features],
      ["Factors to review", data.summary.negative_impact_features],
    ];
    rows.forEach(([label, value]) => {
      const row = document.createElement("p");
      row.textContent = `${label}: ${value ?? 0}`;
      summary.append(row);
    });
    card.append(summary);
  }
  limeResults.append(card);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  setLoading(true, "Finding a crop to explore…");
  limeResults.replaceChildren();
  try {
    showPrediction(await request("predict", getFormData()));
  } catch (error) {
    showError(error.message || "We couldn’t complete the prediction. Please try again.");
  } finally {
    setLoading(false);
  }
});

explainButton.addEventListener("click", async () => {
  if (!form.reportValidity()) return;
  setLoading(true, "Looking at what shaped the recommendation…");
  limeResults.replaceChildren();
  try {
    showExplanation(await request("explain", getFormData()));
  } catch (error) {
    showError(error.message || "We couldn’t prepare an explanation. Please try again.");
  } finally {
    setLoading(false);
  }
});
