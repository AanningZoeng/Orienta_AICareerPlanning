/**
 * Main application logic
 * Coordinates between UI, BubbleEngine, DetailView, and API
 */

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
let careerData = null;
let bubbleEngine = null;
let detailView = null;
let currentMajor = null;
let currentCareer = null;

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize components
    bubbleEngine = new BubbleEngine('bubbleCanvas');
    detailView = new DetailView();

    // Setup event handlers
    setupFormHandler();
    setupBubbleClickHandler();

    console.log('✅ AI Career Path Planner initialized');
});

/**
 * Setup form submission handler
 */
function setupFormHandler() {
    const form = document.getElementById('careerForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnIcon = analyzeBtn.querySelector('.btn-icon');
    const btnLoader = analyzeBtn.querySelector('.btn-loader');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const userQuery = document.getElementById('userQuery').value.trim();
        if (!userQuery) {
            alert('Please describe your interests and goals');
            return;
        }

        // Show loading state
        analyzeBtn.disabled = true;
        btnIcon.style.display = 'none';
        btnLoader.style.display = 'flex';
        showLoadingOverlay();

        try {
            // Call API
            const response = await fetch(`${API_BASE_URL}/analyze`, {
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
            careerData = data;

            // Display results
            displayMajors(data.majors);

        } catch (error) {
            console.error('Error analyzing career path:', error);
            alert('Failed to analyze career path. Make sure the API server is running on localhost:5000');
        } finally {
            // Hide loading state
            analyzeBtn.disabled = false;
            btnIcon.style.display = '';
            btnLoader.style.display = 'none';
            hideLoadingOverlay();
        }
    });
}

/**
 * Setup bubble click handler
 */
function setupBubbleClickHandler() {
    bubbleEngine.onBubbleClick = (bubble) => {
        console.log('Bubble clicked:', bubble);

        if (bubble.type === 'major') {
            // Show major detail in modal
            detailView.showMajorDetail(bubble.data);

            // Also navigate to careers for this major
            currentMajor = bubble.data;
            displayCareers(bubble.data.careers || []);

        } else if (bubble.type === 'career') {
            // Show career detail in modal
            detailView.showCareerDetail(bubble.data);

            // Also navigate to future paths for this career
            currentCareer = bubble.data;
            displayFuturePaths(bubble.data.future_paths || []);

        } else if (bubble.type === 'future') {
            // Show future path detail in modal
            detailView.showFutureDetail(bubble.data);
        }
    };
}

/**
 * Display major bubbles
 */
function displayMajors(majors) {
    if (!majors || majors.length === 0) {
        alert('No majors found. Please try a different query.');
        return;
    }

    currentMajor = null;
    currentCareer = null;

    // Show visualization section
    document.getElementById('searchSection').style.display = 'none';
    document.getElementById('visualizationSection').style.display = 'block';

    // Update breadcrumb
    updateBreadcrumb('Majors');

    // Display bubbles
    bubbleEngine.showMajors(majors);

    console.log(`Displaying ${majors.length} major bubbles`);
}

/**
 * Display career bubbles for a major
 */
function displayCareers(careers) {
    if (!careers || careers.length === 0) {
        console.log('No careers found for this major');
        return;
    }

    currentCareer = null;

    // Update breadcrumb
    updateBreadcrumb('Majors', currentMajor.name, 'Careers');

    // Display bubbles
    bubbleEngine.showCareers(careers, currentMajor.name);

    console.log(`Displaying ${careers.length} career bubbles for ${currentMajor.name}`);
}

/**
 * Display future path bubbles for a career
 */
function displayFuturePaths(futurePaths) {
    if (!futurePaths || futurePaths.length === 0) {
        console.log('No future paths found for this career');
        return;
    }

    // Update breadcrumb
    updateBreadcrumb('Majors', currentMajor.name, 'Careers', currentCareer.title, 'Future Paths');

    // Display bubbles
    bubbleEngine.showFutures(futurePaths, currentCareer.title);

    console.log(`Displaying ${futurePaths.length} future path bubbles for ${currentCareer.title}`);
}

/**
 * Update breadcrumb navigation
 */
function updateBreadcrumb(...items) {
    const breadcrumb = document.getElementById('breadcrumb');

    const html = items.map((item, index) => {
        const isActive = index === items.length - 1;
        return `<span class="breadcrumb-item ${isActive ? 'active' : ''}">${item}</span>`;
    }).join('');

    breadcrumb.innerHTML = html;

    // Make breadcrumb items clickable to navigate back
    const breadcrumbItems = breadcrumb.querySelectorAll('.breadcrumb-item');
    breadcrumbItems.forEach((item, index) => {
        if (index < items.length - 1) {
            item.style.cursor = 'pointer';
            item.addEventListener('click', () => {
                if (index === 0) {
                    // Navigate to majors
                    displayMajors(careerData.majors);
                } else if (index === 2 && currentMajor) {
                    // Navigate to careers
                    displayCareers(currentMajor.careers);
                }
            });
        }
    });
}

/**
 * Show loading overlay
 */
function showLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    document.getElementById('loadingOverlay').style.display = 'none';
}
