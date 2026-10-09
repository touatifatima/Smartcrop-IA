// document.getElementById("predictionForm").addEventListener("submit", function(event) {
//   event.preventDefault();
//<strong>💧 Calculated Humidity:</strong> ${result.humidity_calculated.toFixed(1)}%
//   const data = {
//     N: parseFloat(document.getElementById("N").value),
//     P: parseFloat(document.getElementById("P").value),
//     K: parseFloat(document.getElementById("K").value),
//     temperature: parseFloat(document.getElementById("temperature").value),
//     humidity: parseFloat(document.getElementById("humidity").value),
//     ph: parseFloat(document.getElementById("ph").value),
//     rainfall: parseFloat(document.getElementById("rainfall").value),
//   };

//   fetch("http://127.0.0.1:5000/predict", {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json"
//     },
//     body: JSON.stringify(data)
//   })
//     .then(response => response.json())
//     .then(result => {
//       document.getElementById("result").innerText = "Predicted Crop: " + result.prediction;
//     })
//     .catch(error => {
//       console.error("Error:", error);
//       document.getElementById("result").innerText = "An error occurred while predicting.";
//     });
// });
 
   
                // Get form data function
        function getFormData() {
            return {
                N: parseFloat(document.getElementById("N").value),
                P: parseFloat(document.getElementById("P").value),
                K: parseFloat(document.getElementById("K").value),
                temperature: parseFloat(document.getElementById("temperature").value),
                rainfall: parseFloat(document.getElementById("rainfall").value),
                ph: parseFloat(document.getElementById("ph").value),
                Humidity_calculated: parseFloat(document.getElementById("humidity").value),
                State_Name: document.getElementById("State_Name").value,
                Crop_Type: document.getElementById("Crop_Type").value,
                Area_in_hectares: parseFloat(document.getElementById("area").value),
                Production_in_tons: parseFloat(document.getElementById("production").value),
                Yield_ton_per_hec: parseFloat(document.getElementById("yield").value),
            };
        }

        // Show loading state
        function showLoading(show = true) {
            const loadingDiv = document.getElementById("loadingDiv");
            const predictBtn = document.getElementById("predictBtn");
            const explainBtn = document.getElementById("explainBtn");
            
            if (show) {
                loadingDiv.classList.add("show");
                predictBtn.disabled = true;
                explainBtn.disabled = true;
            } else {
                loadingDiv.classList.remove("show");
                predictBtn.disabled = false;
                explainBtn.disabled = false;
            }
        }

        // Display result
        function displayResult(message, isError = false) {
            const resultDiv = document.getElementById("result");
            const className = isError ? "error" : "success";
            resultDiv.innerHTML = `<div class="${className}">${message}</div>`;
        }

        // Display LIME results
        function displayLimeResults(limeData) {
            const limeDiv = document.getElementById("limeResults");
            
            if (limeData.status === "error") {
                limeDiv.innerHTML = `<div class="error">LIME Explanation Error: ${limeData.error_message}</div>`;
                return;
            }

            let html = `
                <div class="lime-results">
                    <h2>🧠 AI Explanation for: ${limeData.predicted_crop}</h2>
                    
                    <div class="lime-image">
                        <img src="data:image/png;base64,${limeData.visualization.image_base64}" alt="LIME Explanation Chart">
                    </div>
                    
                    <div class="advice-section">
                        <div class="advice-title">🌱 Personalized Farming Advice</div>
            `;
            
            limeData.top_advice.forEach(advice => {
                html += `<div class="advice-item">${advice}</div>`;
            });
            
            html += `
                    </div>
                    
                    <div class="result-card">
                        <h3>📊 Analysis Summary</h3>
                        <p><strong>Total Features Analyzed:</strong> ${limeData.summary.total_features_analyzed}</p>
                        <p><strong>Positive Impact Features:</strong> ${limeData.summary.positive_impact_features}</p>
                        <p><strong>Negative Impact Features:</strong> ${limeData.summary.negative_impact_features}</p>
                        <p><strong>Neutral Impact Features:</strong> ${limeData.summary.neutral_impact_features}</p>
                    </div>
                </div>
            `;
            
            limeDiv.innerHTML = html;
        }

        // Predict crop
        document.getElementById("predictionForm").addEventListener("submit", function(event) {
            event.preventDefault();
            showLoading(true);
            
            const data = getFormData();
            
            axios.post("http://localhost:8000/predict", data, {
                headers: {
                    "Content-Type": "application/json"
                }
            })
            .then(response => {
                showLoading(false);
                const result = response.data;
                displayResult(`
                    <strong>🎯 Recommmended Crop:</strong> ${result.predicted_crop}<br>
                    <strong>🎯 Confidence:</strong> ${(result.confidence * 100).toFixed(1)}%<br>
                    
                `);
            })
            .catch(error => {
                showLoading(false);
                console.error("Error:", error);
                displayResult("❌ An error occurred while predicting. Please check your connection and try again.", true);
            });
        });

        // Explain with LIME
        document.getElementById("explainBtn").addEventListener("click", function() {
            showLoading(true);
            
            const data = getFormData();
            
            axios.post("http://localhost:8000/explain", data, {
                headers: {
                    "Content-Type": "application/json"
                }
            })
            .then(response => {
                showLoading(false);
                displayLimeResults(response.data);
            })
            .catch(error => {
                showLoading(false);
                console.error("LIME Error:", error);
                displayResult("❌ An error occurred while generating explanation. Please try again.", true);
            });
        });
  


