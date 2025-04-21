document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const queryInput = document.getElementById('query-input');
    const searchButton = document.getElementById('search-button');
    const loadingContainer = document.getElementById('loading-container');
    const resultsContainer = document.getElementById('results-container');
    const progressItems = document.getElementById('progress-items');
    const summaryContent = document.getElementById('summary-content');
    const reportContent = document.getElementById('report-content');
    const followUpContent = document.getElementById('follow-up-content');
    const tabButtons = document.querySelectorAll('.tab-button');
    
    // API endpoint (adjust if needed)
    const API_URL = '/research';
    const UPDATES_URL = '/research/';
    
    // Track progress items
    let progressItemsMap = {};
    
    // Current research ID
    let currentResearchId = null;
    let eventSource = null;
    
    // Initialize marked.js with highlight.js
    const markedOptions = {
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true
    };
    
    // Event listeners
    searchButton.addEventListener('click', startResearch);
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            startResearch();
        }
    });
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons and content
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
    
    // Follow-up question click handler
    followUpContent.addEventListener('click', function(e) {
        if (e.target.tagName === 'LI') {
            queryInput.value = e.target.textContent;
            startResearch();
        }
    });
    
    // Start research function
    async function startResearch() {
        console.log('Starting research...');
        const query = queryInput.value.trim();
        if (!query) {
            console.log('Query is empty');
            return;
        }
        
        // Reset UI
        resetUI();
        
        // Show loading container
        loadingContainer.classList.remove('hidden');
        console.log('Loading container shown');
        
        try {
            console.log('Sending research request to:', API_URL);
            // Send research request
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error('Failed to start research');
            }
            
            const data = await response.json();
            console.log('Research ID:', data.research_id);
            currentResearchId = data.research_id;
            
            // Connect to SSE for updates
            connectToEventSource(currentResearchId);
            
        } catch (error) {
            console.error('Error starting research:', error);
            addProgressItem('error', 'Error starting research: ' + error.message, true);
        }
    }
    
    // Connect to event source for updates
    function connectToEventSource(researchId) {
        // Close existing connection if any
        if (eventSource) {
            eventSource.close();
        }
        
        console.log('Connecting to SSE endpoint:', `${UPDATES_URL}${researchId}/updates`);
        // Connect to SSE endpoint
        eventSource = new EventSource(`${UPDATES_URL}${researchId}/updates`);
        
        eventSource.onopen = function() {
            console.log('SSE connection opened');
        };
        
        eventSource.onmessage = function(event) {
            console.log('SSE message received:', event.data);
            const data = JSON.parse(event.data);
            
            if (data.error) {
                console.error('SSE error:', data.error);
                addProgressItem('error', data.error, true);
                return;
            }
            
            handleUpdate(data);
        };
        
        eventSource.onerror = function(error) {
            console.error('EventSource failed:', error);
            eventSource.close();
        };
    }
    
    // Handle update from SSE
    function handleUpdate(update) {
        switch (update.type) {
            case 'trace_id':
                addProgressItem('trace_id', update.content, update.is_done);
                break;
                
            case 'starting':
                addProgressItem('starting', update.content, update.is_done);
                break;
                
            case 'planning':
                updateProgressItem('planning', update.content, update.is_done);
                break;
                
            case 'searching':
                updateProgressItem('searching', update.content, update.is_done);
                break;
                
            case 'writing':
                updateProgressItem('writing', update.content, update.is_done);
                break;
                
            case 'final_report':
                updateProgressItem('final_report', update.content, update.is_done);
                summaryContent.innerHTML = `<div class="report-summary">${update.content}</div>`;
                loadingContainer.classList.add('hidden');
                resultsContainer.classList.remove('hidden');
                break;
                
            case 'full_report':
                reportContent.innerHTML = marked.parse(update.content, markedOptions);
                // Apply syntax highlighting to code blocks
                document.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightBlock(block);
                });
                break;
                
            case 'follow_up_questions':
                const questions = update.content.split('\n').filter(q => q.trim());
                const questionsList = questions.map(q => `<li>${q}</li>`).join('');
                followUpContent.innerHTML = `<ul>${questionsList}</ul>`;
                
                // Close the event source when everything is done
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                break;
        }
    }
    
    // Add a new progress item
    function addProgressItem(id, content, isDone = false) {
        if (progressItemsMap[id]) {
            updateProgressItem(id, content, isDone);
            return;
        }
        
        const itemElement = document.createElement('div');
        itemElement.className = `progress-item ${isDone ? 'done' : ''}`;
        
        let iconHtml = '';
        if (isDone) {
            iconHtml = '<i class="fas fa-check-circle progress-icon"></i>';
        } else {
            iconHtml = '<div class="progress-spinner"></div>';
        }
        
        itemElement.innerHTML = `
            ${iconHtml}
            <div class="progress-content">${content}</div>
        `;
        
        progressItems.appendChild(itemElement);
        progressItemsMap[id] = itemElement;
        
        // Scroll to bottom of progress items
        progressItems.scrollTop = progressItems.scrollHeight;
    }
    
    // Update an existing progress item
    function updateProgressItem(id, content, isDone = false) {
        const itemElement = progressItemsMap[id];
        if (!itemElement) {
            addProgressItem(id, content, isDone);
            return;
        }
        
        const contentElement = itemElement.querySelector('.progress-content');
        contentElement.textContent = content;
        
        if (isDone && !itemElement.classList.contains('done')) {
            itemElement.classList.add('done');
            const spinner = itemElement.querySelector('.progress-spinner');
            if (spinner) {
                spinner.remove();
                itemElement.insertAdjacentHTML('afterbegin', '<i class="fas fa-check-circle progress-icon"></i>');
            }
        }
    }
    
    // Reset UI for new research
    function resetUI() {
        // Clear progress items
        progressItems.innerHTML = '';
        progressItemsMap = {};
        
        // Clear results
        summaryContent.innerHTML = '';
        reportContent.innerHTML = '';
        followUpContent.innerHTML = '';
        
        // Hide results container
        resultsContainer.classList.add('hidden');
        
        // Close existing event source
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    }
});
