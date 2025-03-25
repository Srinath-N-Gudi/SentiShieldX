document.getElementById('analysis-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const url = document.getElementById('youtube-url').value;
  
  // Hide form and show persistent spinner
  document.querySelector('.ytca-form').style.display = 'none';
  document.getElementById('results-section').innerHTML = `
    <div class="loading-spinner">
      <div class="spinner"></div>
      <p>Analyzing comments... Please wait</p>
    </div>
  `;
  document.getElementById('results-section').style.display = 'block';

  try {
    // Real API call
    const response = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `url=${encodeURIComponent(url)}`
    });
    
    if (!response.ok) throw new Error('Analysis failed');
    
    const data = await response.json();
    showResults(data); // Only hides spinner when results arrive
    
  } catch (error) {
    document.getElementById('results-section').innerHTML = `
      <div class="error">
        <p>❌ ${error.message}</p>
        <button class="retry-btn" onclick="window.location.reload()">Try Again</button>
      </div>
    `;
  }
});
function showResults(data) {
  // Determine verdict (pure positive percentage based)
  const isNegative = data.hate > 50;
  
  // Update UI
  document.getElementById('results-section').innerHTML = `
    <div class="results-container">
      <div class="chart-container">
        <canvas id="sentimentChart"></canvas>
      </div>
      <div class="analysis-description">
        <h3 style="color: #d27b7b;">Analysis Results</h3>
        <p>
          <strong>${data.positive}% Positive</strong> | 
          ${data.neutral}% Neutral | 
          ${data.hate}% Hate
        </p>
        <div class="verdict-box ${isNegative ? 'negative' : 'positive'}">
          ${isNegative ? '⚠️ Not Liked (Positive ≤50%)':'✅ Liked (Positive >50%)'}
        </div>
      </div>
    </div>
  `;

  // Render pie chart
  const ctx = document.getElementById('sentimentChart').getContext('2d');
  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Hate', 'Positive', 'Neutral'],
      datasets: [{
        data: [data.hate, data.positive, data.neutral],
        backgroundColor: [
          '#ff4d4d', // Hate (red)
          '#4CAF50',  // Positive (green)
          '#FFC107'   // Neutral (yellow)
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: 'white' }
        }
      }
    }
  });
}