document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingError = document.getElementById('loadingError');
    const databaseConnections = document.getElementById('databaseConnections');
    const llmConfigurations = document.getElementById('llmConfigurations');
    
    // Check application initialization status
    async function checkAppStatus() {
        try {
            const response = await fetch('/api/llms/status');
            const data = await response.json();
            
            if (!data.status.is_loading) {
                // Hide loading overlay
                loadingOverlay.style.display = 'none';
                
                // Show error if there was one
                if (data.status.loading_error) {
                    console.error('Initialization error:', data.status.loading_error);
                    
                    // Show error message
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.textContent = `Warning: There was an error during initialization: ${data.status.loading_error}`;
                    
                    // Insert before the database connections section
                    const mainContent = document.querySelector('main');
                    mainContent.insertBefore(errorDiv, mainContent.firstChild);
                }
            } else {
                // Check again in 1 second
                setTimeout(checkAppStatus, 1000);
            }
        } catch (e) {
            console.error('Error checking app status:', e);
            loadingError.textContent = 'Error connecting to server. Please refresh the page.';
            loadingError.style.display = 'block';
        }
    }
    
    // Load databases function
    async function loadDatabases() {
        try {
            const response = await fetch('/api/databases');
            const databases = await response.json();
            
            let html = '';
            
            if (databases.length === 0) {
                html = '<div class="alert alert-info">No database connections available. Add one to get started.</div>';
            } else {
                databases.forEach(db => {
                    html += `
                    <div class="db-item">
                        <div class="row">
                            <div class="col-md-8">
                                <h5>${db.name}</h5>
                                <div><strong>Type:</strong> ${db.type}</div>
                                ${db.description ? `<div><small>${db.description}</small></div>` : ''}
                            </div>
                            <div class="col-md-4 actions">
                                <button class="btn btn-sm btn-danger delete-db" data-id="${db.id}">
                                    <i class="bi bi-trash"></i> Remove
                                </button>
                            </div>
                        </div>
                    </div>
                    `;
                });
            }
            
            databaseConnections.innerHTML = html;
            
            // Add event listeners to delete buttons
            document.querySelectorAll('.delete-db').forEach(button => {
                button.addEventListener('click', async function() {
                    const id = this.dataset.id;
                    if (confirm('Are you sure you want to remove this database connection?')) {
                        try {
                            const response = await fetch(`/api/databases/${id}`, {
                                method: 'DELETE'
                            });
                            
                            if (response.ok) {
                                loadDatabases();
                            } else {
                                alert('Error removing database connection');
                            }
                        } catch (e) {
                            console.error('Error:', e);
                            alert('Error removing database connection');
                        }
                    }
                });
            });
        } catch (error) {
            console.error('Error loading databases:', error);
            databaseConnections.innerHTML = '<div class="alert alert-danger">Error loading database connections</div>';
        }
    }
    
    // Load LLMs function
    async function loadLLMs() {
        try {
            const response = await fetch('/api/llms');
            const llms = await response.json();
            
            let html = '';
            
            if (llms.length === 0) {
                html = '<div class="alert alert-info">No LLM configurations available. Add one to get started.</div>';
            } else {
                llms.forEach(llm => {
                    html += `
                    <div class="llm-item">
                        <div class="row">
                            <div class="col-md-8">
                                <h5>${llm.name}</h5>
                                <div><strong>Provider:</strong> ${llm.provider}</div>
                                <div><strong>Model:</strong> ${llm.model}</div>
                                ${llm.description ? `<div><small>${llm.description}</small></div>` : ''}
                            </div>
                            <div class="col-md-4 actions">
                                <button class="btn btn-sm btn-danger delete-llm" data-id="${llm.id}">
                                    <i class="bi bi-trash"></i> Remove
                                </button>
                            </div>
                        </div>
                    </div>
                    `;
                });
            }
            
            llmConfigurations.innerHTML = html;
            
            // Add event listeners to delete buttons
            document.querySelectorAll('.delete-llm').forEach(button => {
                button.addEventListener('click', async function() {
                    const id = this.dataset.id;
                    if (confirm('Are you sure you want to remove this LLM configuration?')) {
                        try {
                            const response = await fetch(`/api/llms/${id}`, {
                                method: 'DELETE'
                            });
                            
                            if (response.ok) {
                                loadLLMs();
                            } else {
                                const data = await response.json();
                                alert(`Error: ${data.detail || 'Unknown error'}`);
                            }
                        } catch (e) {
                            console.error('Error:', e);
                            alert('Error removing LLM configuration');
                        }
                    }
                });
            });
        } catch (error) {
            console.error('Error loading LLMs:', error);
            llmConfigurations.innerHTML = '<div class="alert alert-danger">Error loading LLM configurations</div>';
        }
    }
    
    // Add Database form submission
    const saveDatabase = document.getElementById('saveDatabase');
    saveDatabase.addEventListener('click', async function() {
        const dbName = document.getElementById('dbName').value;
        const dbType = document.getElementById('dbType').value;
        const dbConnectionString = document.getElementById('dbConnectionString').value;
        const dbDescription = document.getElementById('dbDescription').value;
        
        if (!dbName || !dbType || !dbConnectionString) {
            alert('Please fill in all required fields');
            return;
        }
        
        try {
            const response = await fetch('/api/databases', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: dbName,
                    type: dbType,
                    connection_string: dbConnectionString,
                    description: dbDescription
                })
            });
            
            if (response.ok) {
                // Clear form
                document.getElementById('dbName').value = '';
                document.getElementById('dbConnectionString').value = '';
                document.getElementById('dbDescription').value = '';
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addDatabaseModal'));
                modal.hide();
                
                // Reload databases
                loadDatabases();
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (e) {
            console.error('Error:', e);
            alert('Error adding database connection');
        }
    });
    
    // Add LLM form submission
    const saveLLM = document.getElementById('saveLLM');
    saveLLM.addEventListener('click', async function() {
        const llmName = document.getElementById('llmName').value;
        const llmProvider = document.getElementById('llmProvider').value;
        const llmModel = document.getElementById('llmModel').value;
        const llmApiKey = document.getElementById('llmApiKey').value;
        const llmDescription = document.getElementById('llmDescription').value;
        
        if (!llmName || !llmProvider || !llmModel) {
            alert('Please fill in all required fields');
            return;
        }
        
        try {
            const response = await fetch('/api/llms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: llmName,
                    provider: llmProvider,
                    model: llmModel,
                    api_key: llmApiKey || null,
                    description: llmDescription,
                    config: {}
                })
            });
            
            if (response.ok) {
                // Clear form
                document.getElementById('llmName').value = '';
                document.getElementById('llmModel').value = '';
                document.getElementById('llmApiKey').value = '';
                document.getElementById('llmDescription').value = '';
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addLLMModal'));
                modal.hide();
                
                // Reload LLMs
                loadLLMs();
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (e) {
            console.error('Error:', e);
            alert('Error adding LLM configuration');
        }
    });
    
    // Initialize
    checkAppStatus();
    loadDatabases();
    loadLLMs();
});
