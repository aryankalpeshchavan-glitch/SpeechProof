function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

async function runAnalyze() {
    const fileInput = document.getElementById('analyze-file');
    if (!fileInput.files.length) {
        alert("Please select a file first.");
        return;
    }
    
    const resultsDiv = document.getElementById('analyze-results');
    resultsDiv.innerText = "Analyzing... (this may take a moment if the model is loading)";
    
    const formData = new FormData();
    formData.append("audio", fileInput.files[0]);
    
    try {
        const response = await fetch('/score', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        resultsDiv.innerText = JSON.stringify(data, null, 2);
    } catch (e) {
        resultsDiv.innerText = "Error: " + e.message;
    }
}

async function runCompare() {
    const refFile = document.getElementById('compare-ref-file');
    const candFile = document.getElementById('compare-cand-file');
    
    if (!refFile.files.length || !candFile.files.length) {
        alert("Please select both a reference and a candidate file.");
        return;
    }
    
    const resultsDiv = document.getElementById('compare-results');
    resultsDiv.innerText = "Comparing... (scoring both recordings)";
    
    const formData = new FormData();
    formData.append("reference", refFile.files[0]);
    formData.append("candidate", candFile.files[0]);
    
    try {
        const response = await fetch('/compare', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        resultsDiv.innerText = JSON.stringify(data, null, 2);
    } catch (e) {
        resultsDiv.innerText = "Error: " + e.message;
    }
}

async function runCrashTest() {
    const fileInput = document.getElementById('crash-file');
    if (!fileInput.files.length) {
        alert("Please select an audio file first.");
        return;
    }
    
    const type = document.getElementById('crash-type').value;
    const intensity = document.getElementById('crash-intensity').value;
    
    const resultsDiv = document.getElementById('crash-results');
    resultsDiv.innerText = "Running crash test transformation and scoring... (this may take a moment)";
    
    const formData = new FormData();
    formData.append("audio", fileInput.files[0]);
    formData.append("transform_type", type);
    formData.append("intensity", intensity);
    
    try {
        const response = await fetch('/arena/transform', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        resultsDiv.innerText = JSON.stringify(data, null, 2);
    } catch (e) {
        resultsDiv.innerText = "Error: " + e.message;
    }
}

async function loadHistory() {
    const resultsDiv = document.getElementById('history-results');
    resultsDiv.innerText = "Loading history...";
    
    try {
        const response = await fetch('/leaderboard');
        const data = await response.json();
        resultsDiv.innerText = JSON.stringify(data, null, 2);
    } catch (e) {
        resultsDiv.innerText = "Error: " + e.message;
    }
}
