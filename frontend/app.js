const API_BASE = "http://localhost:8000";

document.getElementById('workflow-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = document.getElementById('prompt').value;
    const runBtn = document.getElementById('run-btn');
    
    // Disable submit while running
    runBtn.disabled = true;
    runBtn.innerText = "Running...";
    
    try {
        const response = await fetch(`${API_BASE}/api/workflows/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        
        if (!response.ok) throw new Error("Failed to start workflow");
        
        const { job_id } = await response.json();
        startWorkflowStream(job_id, prompt);
    } catch (err) {
        alert(err.message);
        runBtn.disabled = false;
        runBtn.innerText = "Run Workflow";
    }
});

function startWorkflowStream(jobId, prompt) {
    const badge = document.getElementById('workflow-badge');
    const title = document.getElementById('workflow-title');
    const jobIdDisplay = document.getElementById('job-id-display');
    const timeline = document.getElementById('timeline');
    const inspector = document.getElementById('code-inspector');
    
    badge.className = "badge running";
    badge.innerText = "Running";
    title.innerText = "Feature Development Pipeline";
    jobIdDisplay.innerText = `Job ID: ${jobId}`;
    inspector.classList.remove('active');
    
    // Render initial V1 workflow timeline in pending state
    const steps = ["Planner", "Builder", "Reviewer"];
    timeline.innerHTML = steps.map(step => `
        <div class="timeline-step pending" id="step-${step}">
            <div class="step-status">○</div>
            <div class="step-details">
                <div class="step-header">
                    <h4>${step} Step</h4>
                    <span class="duration" id="duration-${step}">Pending</span>
                </div>
                <div class="step-log" id="log-${step}">Waiting to start...</div>
            </div>
        </div>
    `).join('');
    
    // Connect to SSE stream
    const eventSource = new EventSource(`${API_BASE}/api/workflows/${jobId}/stream`);
    let startTime = null;
    let artifacts = {};

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("SSE Event:", data);
        
        switch (data.event_type) {
            case "WorkflowStarted":
                startTime = Date.now();
                break;
                
            case "StepStarted":
                const runningStep = document.getElementById(`step-${data.step_name}`);
                if (runningStep) {
                    runningStep.className = "timeline-step running";
                    runningStep.querySelector('.step-status').innerText = "↻";
                    document.getElementById(`log-${data.step_name}`).innerText = "Executing agent logic...";
                    document.getElementById(`duration-${data.step_name}`).innerText = "In Progress";
                }
                break;
                
            case "StepFinished":
                const completedStep = document.getElementById(`step-${data.step_name}`);
                if (completedStep) {
                    completedStep.className = "timeline-step completed";
                    completedStep.querySelector('.step-status').innerText = "✓";
                    document.getElementById(`duration-${data.step_name}`).innerText = "Success";
                    
                    const logElement = document.getElementById(`log-${data.step_name}`);
                    
                    // Render specific payloads nicely
                    if (data.step_name === "Planner" && data.payload) {
                        const spec = data.payload;
                        logElement.innerHTML = `
<strong>Description:</strong> ${spec.description}
<strong>Tasks:</strong>
${spec.tasks.map(t => `- ${t}`).join('\n')}
<strong>Files to Create:</strong>
${spec.files_to_create.map(f => `- ${f}`).join('\n')}
<strong>Constraints:</strong>
${spec.constraints.map(c => `- ${c}`).join('\n')}
                        `.trim();
                    } else if (data.step_name === "Builder" && data.payload) {
                        artifacts = data.payload;
                        logElement.innerText = `Generated files: ${Object.keys(artifacts).join(', ')}`;
                    } else if (data.step_name === "Reviewer" && data.payload) {
                        logElement.innerText = data.payload;
                    }
                }
                break;
                
            case "WorkflowCompleted":
                eventSource.close();
                badge.className = "badge success";
                badge.innerText = "Completed";
                document.getElementById('run-btn').disabled = false;
                document.getElementById('run-btn').innerText = "Run Workflow";
                
                // Show artifacts if any were generated
                if (Object.keys(artifacts).length > 0) {
                    renderInspector(artifacts);
                }
                break;
                
            case "WorkflowFailed":
                eventSource.close();
                badge.className = "badge failed";
                badge.innerText = "Failed";
                document.getElementById('run-btn').disabled = false;
                document.getElementById('run-btn').innerText = "Run Workflow";
                
                // Set the active progress step to failed
                const activeStep = document.querySelector('.timeline-step.running');
                if (activeStep) {
                    activeStep.className = "timeline-step failed";
                    activeStep.querySelector('.step-status').innerText = "✗";
                    activeStep.querySelector('.step-log').innerText = `Error: ${data.payload.error}`;
                }
                break;
        }
    };
    
    eventSource.onerror = (err) => {
        console.error("SSE Connection Error:", err);
        eventSource.close();
        badge.className = "badge failed";
        badge.innerText = "Connection Lost";
        document.getElementById('run-btn').disabled = false;
        document.getElementById('run-btn').innerText = "Run Workflow";
    };
}

function renderInspector(files) {
    const inspector = document.getElementById('code-inspector');
    const tabsContainer = document.getElementById('file-tabs');
    const codeBlock = document.getElementById('code-block');
    
    inspector.classList.add('active');
    tabsContainer.innerHTML = "";
    
    const fileNames = Object.keys(files);
    
    fileNames.forEach((fileName, index) => {
        const button = document.createElement('button');
        button.className = `tab-btn ${index === 0 ? 'active' : ''}`;
        button.innerText = fileName;
        button.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            codeBlock.innerText = files[fileName];
        });
        tabsContainer.appendChild(button);
    });
    
    // Select first file by default
    if (fileNames.length > 0) {
        codeBlock.innerText = files[fileNames[0]];
    }
}
