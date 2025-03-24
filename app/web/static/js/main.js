document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let selectedDatabaseId = null;
    let selectedLLMId = null;
    
    // DOM elements
    const chatMessages = document.getElementById('chatMessages');
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const reasoningContent = document.getElementById('reasoningContent');
    const schemasContent = document.getElementById('schemasContent');
    const sqlContent = document.getElementById('sqlContent');
    const resultContent = document.getElementById('resultContent');
    const runSqlButton = document.getElementById('runSqlButton');
    const selectedDatabase = document.getElementById('selectedDatabase');
    const databaseList = document.getElementById('databaseList');
    const selectedLLM = document.getElementById('selectedLLM');
    const llmList = document.getElementById('llmList');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingError = document.getElementById('loadingError');
    
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
                    addMessage(`Warning: There was an error during initialization: ${data.status.loading_error}`, 'system');
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
    
    // Try to restore session state
    try {
        const savedDatabaseId = sessionStorage.getItem('selectedDatabaseId');
        if (savedDatabaseId) {
            selectedDatabaseId = savedDatabaseId;
        }
        
        const savedLLMId = sessionStorage.getItem('selectedLLMId');
        if (savedLLMId) {
            selectedLLMId = savedLLMId;
        }
    } catch (e) {
        console.error('Error restoring session:', e);
    }
    
    // Load databases
    async function loadDatabases() {
        try {
            const response = await fetch('/api/databases');
            const databases = await response.json();
            
            // Clear database list
            databaseList.innerHTML = '';
            
            if (databases.length === 0) {
                databaseList.innerHTML = '<li><a class="dropdown-item" href="#">No databases available</a></li>';
                selectedDatabaseId = null;
                selectedDatabase.textContent = 'No Database';
                sessionStorage.removeItem('selectedDatabaseId');
                return;
            }
            
            // Add databases to dropdown
            databases.forEach(db => {
                const item = document.createElement('li');
                const link = document.createElement('a');
                link.classList.add('dropdown-item');
                link.href = '#';
                link.textContent = db.name;
                link.dataset.id = db.id;
                
                link.addEventListener('click', function() {
                    selectedDatabaseId = db.id;
                    selectedDatabase.textContent = db.name;
                    // Save to session storage
                    try {
                        sessionStorage.setItem('selectedDatabaseId', db.id);
                    } catch (e) {
                        console.error('Error saving to session storage:', e);
                    }
                });
                
                item.appendChild(link);
                databaseList.appendChild(item);
            });
            
            // Check if the saved database ID exists in the available databases
            let databaseExists = false;
            if (selectedDatabaseId) {
                databaseExists = databases.some(db => db.id === selectedDatabaseId);
                if (databaseExists) {
                    // Find the database name
                    const db = databases.find(db => db.id === selectedDatabaseId);
                    selectedDatabase.textContent = db.name;
                }
            }
            
            // If no valid database ID, select the first one by default
            if (!databaseExists) {
                selectedDatabaseId = databases[0].id;
                selectedDatabase.textContent = databases[0].name;
                // Save to session storage
                try {
                    sessionStorage.setItem('selectedDatabaseId', databases[0].id);
                } catch (e) {
                    console.error('Error saving to session storage:', e);
                }
            }
        } catch (error) {
            console.error('Error loading databases:', error);
        }
    }
    
    // Load LLMs
    async function loadLLMs() {
        try {
            const response = await fetch('/api/llms');
            const llms = await response.json();
            
            // Clear LLM list
            llmList.innerHTML = '';
            
            if (llms.length === 0) {
                llmList.innerHTML = '<li><a class="dropdown-item" href="#">No LLMs available</a></li>';
                selectedLLMId = null;
                selectedLLM.textContent = 'No LLM';
                sessionStorage.removeItem('selectedLLMId');
                return;
            }
            
            // Add LLMs to dropdown
            llms.forEach(llm => {
                const item = document.createElement('li');
                const link = document.createElement('a');
                link.classList.add('dropdown-item');
                link.href = '#';
                link.textContent = llm.name;
                link.dataset.id = llm.id;
                
                link.addEventListener('click', function() {
                    selectedLLMId = llm.id;
                    selectedLLM.textContent = llm.name;
                    // Save to session storage
                    try {
                        sessionStorage.setItem('selectedLLMId', llm.id);
                    } catch (e) {
                        console.error('Error saving to session storage:', e);
                    }
                });
                
                item.appendChild(link);
                llmList.appendChild(item);
            });
            
            // Check if the saved LLM ID exists in the available LLMs
            let llmExists = false;
            if (selectedLLMId) {
                llmExists = llms.some(llm => llm.id === selectedLLMId);
                if (llmExists) {
                    // Find the LLM name
                    const llm = llms.find(llm => llm.id === selectedLLMId);
                    selectedLLM.textContent = llm.name;
                }
            }
            
            // If no valid LLM ID, select the first one by default
            if (!llmExists) {
                selectedLLMId = llms[0].id;
                selectedLLM.textContent = llms[0].name;
                // Save to session storage
                try {
                    sessionStorage.setItem('selectedLLMId', llms[0].id);
                } catch (e) {
                    console.error('Error saving to session storage:', e);
                }
            }
        } catch (error) {
            console.error('Error loading LLMs:', error);
        }
    }
    
    // Process a query
    async function processQuery(query) {
        // Check if database is selected
        if (!selectedDatabaseId) {
            addMessage('Please select a database first.', 'bot');
            return;
        }
        
        // Add user message to chat
        addMessage(query, 'user');
        
        // Clear trace content
        reasoningContent.textContent = 'Processing...';
        schemasContent.innerHTML = 'Processing...';
        sqlContent.textContent = 'Processing...';
        resultContent.innerHTML = 'Processing...';
        
        // Disable run SQL button
        runSqlButton.style.display = 'none';
        
        try {
            // Call API to process query
            const response = await fetch('/api/queries', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    llm_provider: selectedLLMId,
                    should_execute_sql: true,
                    database_id: selectedDatabaseId
                }),
            });
            
            const data = await response.json();
            
            // Check for database not found error
            if (data.error && data.error.includes('Database with ID') && data.error.includes('not found')) {
                // Database ID might have changed, reload databases and try again
                addMessage('Database connection was reset. Reloading databases...', 'bot');
                await loadDatabases();
                if (selectedDatabaseId) {
                    // Retry the query
                    processQuery(query);
                } else {
                    addMessage('No database available. Please add a database connection.', 'bot');
                }
                return;
            }
            
            // Add bot message to chat
            let botMessage = '';
            if (data.success) {
                if (data.result) {
                    botMessage = `I've converted your query to SQL and executed it. Check the result tab for details.`;
                } else {
                    botMessage = `I've converted your query to SQL but didn't execute it. Check the SQL tab for the query.`;
                }
            } else {
                botMessage = `I encountered an error: ${data.error}`;
            }
            
            addMessage(botMessage, 'bot');
            
            // Update trace content
            updateTrace(data);
        } catch (error) {
            console.error('Error processing query:', error);
            addMessage('Sorry, there was an error processing your query. Please try again.', 'bot');
            
            reasoningContent.textContent = 'Error processing query';
            schemasContent.innerHTML = 'Error processing query';
            sqlContent.textContent = 'Error processing query';
            resultContent.innerHTML = 'Error processing query';
        }
    }
    
    // Add a message to the chat
    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add(`${type}-message`);
        messageDiv.textContent = text;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Update trace content
    function updateTrace(data) {
        // Update reasoning
        reasoningContent.textContent = data.trace.reasoning || 'No reasoning available';
        
        // Update retrieved schemas
        if (data.trace.retrieved_schemas && data.trace.retrieved_schemas.length > 0) {
            let schemasHtml = '';
            
            data.trace.retrieved_schemas.forEach(table => {
                schemasHtml += `
                <div class="table-schema">
                    <h5>${table.name}</h5>
                    <div class="column-list">
                `;
                
                table.columns.forEach(column => {
                    const pkClass = column.is_primary_key ? 'column-pk' : '';
                    const fkClass = column.is_foreign_key ? 'column-fk' : '';
                    const pkBadge = column.is_primary_key ? '<span class="badge bg-danger">PK</span> ' : '';
                    const fkBadge = column.is_foreign_key ? `<span class="badge bg-primary">FK</span> ` : '';
                    
                    schemasHtml += `
                    <div class="column-item ${pkClass} ${fkClass}">
                        ${pkBadge}${fkBadge}${column.name}: ${column.data_type}
                        ${column.is_foreign_key && column.references ? `<small>(References: ${column.references})</small>` : ''}
                    </div>
                    `;
                });
                
                schemasHtml += `
                    </div>
                </div>
                `;
            });
            
            schemasContent.innerHTML = schemasHtml;
        } else {
            schemasContent.innerHTML = 'No schemas retrieved';
        }
        
        // Update SQL
        sqlContent.textContent = data.sql || 'No SQL generated';
        
        // Show run SQL button if SQL is available and not executed
        if (data.sql && (!data.result || !data.success)) {
            runSqlButton.style.display = 'inline-block';
            
            // Add event listener to run SQL button
            runSqlButton.onclick = async function() {
                try {
                    const response = await fetch('/api/queries', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            query: data.query,
                            llm_provider: selectedLLMId,
                            should_execute_sql: true,
                            database_id: selectedDatabaseId
                        }),
                    });
                    
                    const newData = await response.json();
                    
                    // Update trace content
                    updateTrace(newData);
                    
                    // Add bot message to chat
                    let botMessage = '';
                    if (newData.success) {
                        botMessage = `I've executed the SQL. Check the result tab for details.`;
                    } else {
                        botMessage = `I encountered an error while executing the SQL: ${newData.error}`;
                    }
                    
                    addMessage(botMessage, 'bot');
                } catch (error) {
                    console.error('Error executing SQL:', error);
                    addMessage('Sorry, there was an error executing the SQL. Please try again.', 'bot');
                }
            };
        } else {
            runSqlButton.style.display = 'none';
        }
        
        // Update result
        if (data.result) {
            if (data.result.columns && data.result.rows) {
                let resultHtml = `
                <div class="result-info mb-3">
                    <span class="badge bg-success">${data.result.row_count} rows returned</span>
                </div>
                <div class="result-table">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                `;
                
                // Add column headers
                data.result.columns.forEach(column => {
                    resultHtml += `<th>${column}</th>`;
                });
                
                resultHtml += `
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                // Add rows
                data.result.rows.forEach(row => {
                    resultHtml += '<tr>';
                    row.forEach(cell => {
                        resultHtml += `<td>${cell !== null ? cell : 'NULL'}</td>`;
                    });
                    resultHtml += '</tr>';
                });
                
                resultHtml += `
                        </tbody>
                    </table>
                </div>
                `;
                
                resultContent.innerHTML = resultHtml;
            } else {
                resultContent.innerHTML = 'No result data available';
            }
        } else if (data.error) {
            resultContent.innerHTML = `<div class="error-message">${data.error}</div>`;
        } else {
            resultContent.innerHTML = 'No result available';
        }
    }
    
    // Event listeners
    
    // Submit query form
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        
        if (query) {
            processQuery(query);
            queryInput.value = '';
        }
    });
    
    // Initialize
    checkAppStatus();
    loadDatabases();
    loadLLMs();
}); 