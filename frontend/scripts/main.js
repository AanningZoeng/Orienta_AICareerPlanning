/**
 * Main application logic for tree-based career path planner
 * Coordinates between UI, TreeEngine, and API
 */

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
let treeEngine = null;
let currentData = {
    majors: null,
    careers: {},  // Keyed by major name
    futurePaths: {}  // Keyed by career node id
};

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌳 Initializing Tree-based Career Path Planner...');
    
    // Initialize tree engine
    treeEngine = new TreeEngine('treeCanvas');
    
    // Setup tree node click handler
    treeEngine.onNodeClick = handleNodeClick;
    
    // Initialize tree with root node
    treeEngine.initializeTree('');
    
    console.log('✅ Tree engine initialized');
});


/**
 * Handle node click events
 */
async function handleNodeClick(node) {
    console.log('Node clicked:', node);
    
    if (node.type === 'root') {
        // Root node clicked - fetch majors
        if (!node.expanded) {
            await fetchAndDisplayMajors(node.userQuery);
        } else {
            // Show root details
            treeEngine.showNodeDetails(node);
        }
        
    } else if (node.type === 'major') {
        // Major node clicked
        if (!node.expanded) {
            // Fetch careers for this major
            await fetchAndDisplayCareers(node);
        } else {
            // Show major details (description + resources)
            treeEngine.showNodeDetails(node);
        }
        
    } else if (node.type === 'career') {
        // Career node clicked
        if (!node.expanded) {
            // Fetch future paths for this career (mock for now)
            fetchAndDisplayFuturePaths(node);
        } else {
            // Show career details (description + resources)
            treeEngine.showNodeDetails(node);
        }
        
    } else if (node.type === 'future') {
        // Future path node clicked - show details
        treeEngine.showNodeDetails(node);
    }
}


/**
 * Fetch and display majors from API
 */
async function fetchAndDisplayMajors(userQuery) {
    if (!userQuery || !userQuery.trim()) {
        alert('Please enter your interests and goals first');
        return;
    }
    
    showLoadingOverlay('🔍 Researching university majors...');
    
    try {
        // Call MajorResearchAgent via API
        const response = await fetch(`${API_BASE_URL}/research-majors`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: userQuery })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Majors data received:', data);
        
        // Store majors data
        currentData.majors = data.majors;
        
        // Add major nodes to tree
        treeEngine.addMajors(data.majors);
        
        hideLoadingOverlay();
        
    } catch (error) {
        console.error('Error fetching majors:', error);
        hideLoadingOverlay();
        alert('Failed to fetch majors. Please check:\n1. Flask server is running on localhost:5000\n2. MajorResearchAgent is configured correctly\n\nError: ' + error.message);
    }
}

/**
 * Fetch and display careers for a major
 */
async function fetchAndDisplayCareers(majorNode) {
    const majorName = majorNode.label;
    
    showLoadingOverlay(`💼 Analyzing careers for ${majorName}...`);
    
    try {
        // Call CareerAnalysisAgent via API
        const response = await fetch(`${API_BASE_URL}/analyze-careers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ major_name: majorName })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Careers data received:', data);
        
        // Store careers data
        currentData.careers[majorName] = data.careers;
        
        // Add career nodes to tree
        treeEngine.addCareers(majorNode.id, data.careers);
        
        hideLoadingOverlay();
        
    } catch (error) {
        console.error('Error fetching careers:', error);
        hideLoadingOverlay();
        alert('Failed to fetch careers. Please check:\n1. Flask server is running\n2. CareerAnalysisAgent is configured\n3. careers_latest.json exists\n\nError: ' + error.message);
    }
}

/**
 * Fetch and display future paths for a career
 */
function fetchAndDisplayFuturePaths(careerNode) {
    // Mock implementation - FuturePathAgent not yet implemented
    showLoadingOverlay('🔮 Projecting future paths...');
    
    setTimeout(() => {
        // Mock future paths
        const mockFutures = [
            {
                title: '5-Year Outlook',
                description: 'Expected growth and opportunities within 5 years',
                resources: []
            },
            {
                title: '10-Year Outlook',
                description: 'Long-term career trajectory and advancement',
                resources: []
            },
            {
                title: 'Industry Trends',
                description: 'Emerging trends affecting this career path',
                resources: []
            }
        ];
        
        currentData.futurePaths[careerNode.id] = mockFutures;
        
        treeEngine.addFuturePaths(careerNode.id, mockFutures);
        
        hideLoadingOverlay();
    }, 1000);
}


/**
 * Show loading overlay
 */
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    const content = overlay.querySelector('.loading-content h3');
    if (content) {
        content.textContent = message;
    }
    overlay.style.display = 'flex';
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'none';
}
