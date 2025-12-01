document.addEventListener('DOMContentLoaded', function() {
    checkStatus();
    loadPendingContent();
    
    // Refresh every 30 seconds
    setInterval(checkStatus, 30000);
});

async def checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        document.getElementById('status-text').innerText = data.status;
        
        // Here you would also fetch counts from a real stats endpoint
    } catch (error) {
        console.error('Error checking status:', error);
        document.getElementById('status-text').innerText = 'Offline';
    }
}

async function loadPendingContent() {
    const queue = document.getElementById('content-queue');
    try {
        const response = await fetch('/api/content/pending');
        const contentList = await response.json();
        
        if (contentList.length === 0) {
            queue.innerHTML = '<p class="text-muted">No content pending approval.</p>';
            return;
        }

        let html = '';
        contentList.forEach(item => {
            html += `
                <div class="content-item">
                    <h4>${item.platform} - ${item.format}</h4>
                    <p class="mb-1"><strong>Topic:</strong> ${item.topic}</p>
                    <div class="p-3 bg-dark rounded mb-3 text-break font-monospace">
                        ${item.content_text}
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-success btn-sm" onclick="approveContent(${item.id})">Approve</button>
                        <button class="btn btn-danger btn-sm" onclick="rejectContent(${item.id})">Reject</button>
                        <button class="btn btn-secondary btn-sm" onclick="editContent(${item.id})">Edit</button>
                    </div>
                </div>
            `;
        });
        queue.innerHTML = html;
    } catch (error) {
        queue.innerHTML = '<p class="text-danger">Error loading content.</p>';
    }
}

async function approveContent(id) {
    if(!confirm('Approve and publish this content?')) return;
    
    try {
        const response = await fetch(`/api/content/approve/${id}`, { method: 'POST' });
        if (response.ok) {
            loadPendingContent(); // Reload list
        } else {
            alert('Failed to approve content');
        }
    } catch (error) {
        alert('Error approving content');
    }
}

async function rejectContent(id) {
    if(!confirm('Reject this content?')) return;
    
    try {
        const response = await fetch(`/api/content/reject/${id}`, { method: 'POST' });
        if (response.ok) {
            loadPendingContent(); 
        }
    } catch (error) {
        alert('Error rejecting content');
    }
}

async function triggerPipeline(type) {
    // Implementation for manual triggers
    alert('Triggering ' + type);
    await fetch('/api/run_pipeline', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phase: 4, agent_name: type === 'market_scan' ? 'MarketScannerAgent' : null})
    });
}
