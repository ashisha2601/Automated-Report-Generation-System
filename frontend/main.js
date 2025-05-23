// =============================
// 1. Global State & Utilities
// =============================
const BACKEND_URL = 'http://localhost:8002';
let isLoggedIn = false;
image.pnglet currentUser = null;
let userHistory = [];

function generateUniqueIdForUser(email) {
    return 'AIF' + Date.now() + '_' + btoa(email).replace(/[^a-zA-Z0-9]/g, '').slice(0, 8);
}

function generateUniqueId() {
    const prefix = 'AIF';
    const year = new Date().getFullYear();
    const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    return `${prefix}${year}${random}`;
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    }).format(new Date(date));
}

// Helper to add entry to history array and update UI if needed
function addHistoryEntry(entry) {
    userHistory.push(entry);
    // Optionally update UI here to show history
    console.log('History added:', entry);
}

// Function to fetch user history from the backend
async function fetchUserHistory() {
    if (!currentUser || !currentUser.userId) {
        console.error('User not logged in or userId is missing.');
        return;
    }
    
    try {
        console.log(`Fetching history for user ${currentUser.userId}...`);
        const response = await fetch(`${BACKEND_URL}/api/history/${currentUser.userId}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to fetch history:', response.status, errorText);
            // Clear table and show an error message to the user
            document.getElementById('historyTableBody').innerHTML = `<tr><td colspan="5">Error loading history: ${response.status}</td></tr>`;
            return;
        }
        
        const historyData = await response.json();
        console.log('History fetched successfully:', historyData);
        renderHistoryTable(historyData);
        
    } catch (error) {
        console.error('Error fetching history:', error);
        // Clear table and show a generic error message
        document.getElementById('historyTableBody').innerHTML = '<tr><td colspan="5">Failed to load history.</td></tr>';
    }
}

// Function to render history data in the table
function renderHistoryTable(historyItems) {
    const tableBody = document.getElementById('historyTableBody');
    tableBody.innerHTML = ''; // Clear existing rows

    if (historyItems.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No history records found.</td></tr>';
        return;
    }

    historyItems.forEach(item => {
        const row = document.createElement('tr');
        
        // Date & Time (Format using the formatDate helper)
        const dateCell = document.createElement('td');
        dateCell.textContent = formatDate(item.created_at);
        row.appendChild(dateCell);
        
        // Activity
        const activityCell = document.createElement('td');
        activityCell.textContent = item.activity_type;
        row.appendChild(activityCell);
        
        // File Name
        const fileNameCell = document.createElement('td');
        fileNameCell.textContent = item.file_name || '-'; // Use '-' if file_name is null
        row.appendChild(fileNameCell);
        
        // Size (Backend doesn't provide size, use placeholder)
        const sizeCell = document.createElement('td');
        sizeCell.textContent = '-'; // Placeholder
        row.appendChild(sizeCell);
        
        // Report ID
        const reportIdCell = document.createElement('td');
        reportIdCell.textContent = item.report_id || '-'; // Use '-' if report_id is null
        if (item.report_id) {
             reportIdCell.classList.add('report-id'); // Add class for styling if needed
        }
        row.appendChild(reportIdCell);
        
        tableBody.appendChild(row);
    });
}

// =============================
// 1A. Daily Assessment: File Upload & Filter Handling
// =============================

async function handleDailyAssessmentFile(file) {
    if (!currentUser) {
        alert('User not logged in.');
        return null;
    }
    const fileId = generateUniqueId();
    const fileData = new FormData();
    fileData.append('file', file);
    fileData.append('userId', currentUser.userId);
    fileData.append('fileId', fileId);

    try {
        const res = await fetch(`${BACKEND_URL}/api/daily-assessment/upload`, {
            method: 'POST',
            body: fileData
        });
        if (!res.ok) throw new Error('Upload failed');
        alert('Daily Assessment file uploaded');

        // Add upload to history
        // addHistoryEntry({
        //     date: new Date(),
        //     activity: 'DA File Upload',
        //     fileName: file.name,
        //     fileSize: file.size,
        //     fileId: fileId,
        //     reportId: '-'
        // });

        // Send history entry to backend
        await fetch(`${BACKEND_URL}/api/history/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.userId,
                activity_type: 'Daily Assessment File Upload',
                file_id: fileId,
                file_name: file.name,
                report_id: null, // No report ID for upload
                filters: {} // No filters for upload
            })
        });
        console.log('File upload history sent to backend.');

        return fileId;

    } catch (err) {
        alert('Upload failed');
        return null;
    }
}

function getSelectedFilters(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    const formData = new FormData(form);
    const filters = {};
    for (let [key, value] of formData.entries()) {
        if (!filters[key]) filters[key] = [];
        filters[key].push(value);
    }
    return filters;
}

async function generateDailyAssessmentReport(relatedFileId = '-') {
    if (!isLoggedIn || !currentUser) {
        showLoginPopup('Please login to generate Daily Assessment report.');
        return;
    }

    const reportId = generateUniqueId();
    const filters = getSelectedFilters('filter-form');

    try {
        const res = await fetch(`${BACKEND_URL}/api/daily-assessment/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: currentUser.userId, filters, reportId })
        });
        if (!res.ok) throw new Error('Failed to generate report');

        addHistoryEntry({
            date: new Date(),
            activity: 'DA Report',
            fileName: 'Daily_Assessment_Report',
            fileSize: '-',
            fileId: relatedFileId,
            reportId: reportId
        });

        alert(`Daily Assessment report generated. ID: ${reportId}`);

    } catch (error) {
        alert('Failed to generate report. Please try again.');
    }
}

// =============================
// 1B. Impact Assessment: File Upload & Filter Handling
// =============================

async function handleImpactAssessmentFile(file) {
    if (!currentUser) {
        alert('User not logged in.');
        return null;
    }
    const fileId = generateUniqueId();
    const fileData = new FormData();
    fileData.append('file', file);
    fileData.append('userId', currentUser.userId);
    fileData.append('fileId', fileId);

    try {
        const res = await fetch(`${BACKEND_URL}/api/impact-assessment/upload`, {
            method: 'POST',
            body: fileData
        });
        if (!res.ok) throw new Error('Upload failed');
        alert('Impact Assessment file uploaded');

        // Add upload to history
        addHistoryEntry({
            date: new Date(),
            activity: 'IA File Upload',
            fileName: file.name,
            fileSize: file.size,
            fileId: fileId,
            reportId: '-'
        });

        return fileId;

    } catch (err) {
        alert('Upload failed');
        return null;
    }
}

async function generateImpactAssessmentReport(relatedFileId = '-') {
    if (!isLoggedIn || !currentUser) {
        showLoginPopup('Please login to generate Impact Assessment report.');
        return;
    }

    const reportId = generateUniqueId();
    const filters = getSelectedFilters('impact-filter-form');

    try {
        const res = await fetch(`${BACKEND_URL}/api/impact-assessment/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: currentUser.userId, filters, reportId })
        });
        if (!res.ok) throw new Error('Failed to generate report');

        addHistoryEntry({
            date: new Date(),
            activity: 'IA Report',
            fileName: 'Impact_Assessment_Report',
            fileSize: '-',
            fileId: relatedFileId,
            reportId: reportId
        });

        alert(`Impact Assessment report generated. ID: ${reportId}`);

    } catch (error) {
        alert('Failed to generate report. Please try again.');
    }
}

// =============================
// 2. Login Handling
// =============================
console.log('--- Entering requestLoginOtp function ---')

async function requestLoginOtp() {
    console.log('--- Entering requestLoginOtp function ---');
    const email = document.getElementById('loginEmail').value;

    if (!email || !email.endsWith('@agastya.org')) {
        alert('Please enter a valid @agastya.org email address');
        console.log('--- Exiting requestLoginOtp due to invalid email ---');
        return;
    }

    console.log('Attempting to send OTP request for:', email);

    try {
        console.log('Making fetch call to:', `${BACKEND_URL}/api/login`);
        const res = await fetch(`${BACKEND_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        console.log('Fetch call completed. Response status:', res.status);

        if (!res.ok) {
            const errorText = await res.text();
            console.error('Failed to send OTP:', res.status, errorText);
            throw new Error(`Failed to send OTP: ${res.status} - ${errorText}`);
        }

        const data = await res.json();
        console.log('OTP request successful:', data);
        document.getElementById('loginOtpContainer').classList.add('active');
        document.getElementById('requestLoginOtp').style.display = 'none';
        document.querySelector('#loginOtpContainer .otp-input[data-index="1"]').focus();
    } catch (error) {
        console.error('Error during OTP request:', error);
        alert('Failed to send OTP. Please check the console for details.');
    }
}

async function verifyLoginOtp() {
    console.log('*** verifyLoginOtp function started ***');
    console.log('--- Entering verifyLoginOtp function ---');
    let otp = '';
    document.querySelectorAll('#loginOtpContainer .otp-input').forEach(input => {
        otp += input.value;
    });

    const email = document.getElementById('loginEmail').value;

    console.log('Verifying OTP for:', email, 'OTP:', otp);

    try {
        const res = await fetch(`${BACKEND_URL}/api/verify-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, otp, userId: generateUniqueIdForUser(email) })
        });

        if (!res.ok) {
            const errorText = await res.text();
            console.error('OTP verification failed:', res.status, errorText);
            throw new Error('Invalid OTP');
        }

        const data = await res.json();
        console.log('OTP verification successful. User data:', data);

        loginUser({
            email: data.email,
            name: data.name,
            userId: data.userId,
            memberSince: data.memberSince || new Date().toDateString()
        });

        console.log('currentUser after loginUser call:', currentUser);

        document.getElementById('login').style.display = 'none';
        document.getElementById('loginPopupOverlay').classList.add('show');
        document.getElementById('loginSuccessPopup').classList.add('show');

        document.getElementById('closeLoginPopup').addEventListener('click', () => {
            document.getElementById('loginPopupOverlay').classList.remove('show');
            document.getElementById('loginSuccessPopup').classList.remove('show');
            document.getElementById('home').scrollIntoView({ behavior: 'smooth' });
        });

        // Removed fetchUserHistory from here, will call when history page is shown
        // fetchUserHistory();

        console.log('--- Exiting verifyLoginOtp function ---');

    } catch (error) {
        console.error('Error during OTP verification:', error);
        alert('Invalid OTP. Please try again.');
    }
}

function loginUser(user) {
    console.log('--- Entering loginUser function ---');
    console.log('User data passed to loginUser:', user);
    isLoggedIn = true;
    currentUser = user;
    console.log('Global currentUser inside loginUser:', currentUser);

    // Store user data in localStorage
    try {
        localStorage.setItem('currentUser', JSON.stringify(user));
        console.log('User data stored in localStorage.');
    } catch (e) {
        console.error('Failed to save user data to localStorage:', e);
    }

    // Update header UI - This part might need to be moved/called elsewhere too
    updateHeaderUI(user);

    console.log('--- Exiting loginUser function ---');
}

// Function to update the header UI after login
function updateHeaderUI(user) {
    document.getElementById('loginBtn').style.display = 'none';
    document.getElementById('userProfile').style.display = 'block';
    document.getElementById('profileIcon').textContent = user.name.charAt(0).toUpperCase();
    document.getElementById('userName').textContent = user.name;
    document.getElementById('userEmail').textContent = user.email;
    document.getElementById('memberSince').textContent = user.memberSince;
    document.getElementById('profilePhoto').querySelector('span').textContent = user.name.charAt(0).toUpperCase();
}

// Function to check login status from localStorage on page load
function checkLoginStatusOnLoad() {
    console.log('--- Checking login status from localStorage ---');
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
            isLoggedIn = true;
            console.log('currentUser restored from localStorage:', currentUser);
            // Update UI to show logged-in state
            updateHeaderUI(currentUser);
        } catch (e) {
            console.error('Error parsing user data from localStorage:', e);
            localStorage.removeItem('currentUser'); // Clear invalid data
            isLoggedIn = false;
            currentUser = null;
        }
    } else {
        isLoggedIn = false;
        currentUser = null;
        console.log('No user data found in localStorage.');
    }
     // Initial UI update based on login status (hide user profile if not logged in)
     if (!isLoggedIn) {
        document.getElementById('loginBtn').style.display = 'block';
        document.getElementById('userProfile').style.display = 'none';
     }
     console.log('--- Finished checking login status ---');
}

function showHistoryPage() {
    console.log('--- Entering showHistoryPage ---');
    console.log('currentUser state in showHistoryPage:', currentUser);

    // Check if currentUser is set before fetching history
    if (!currentUser || !currentUser.userId) {
        console.error('Cannot fetch history: User not logged in or userId is missing.');
        // Optionally redirect to login or show a message
        alert('Please log in to view history.');
        // Clear table and show a message
        document.getElementById('historyTableBody').innerHTML = '<tr><td colspan="5">Please log in to view history.</td></tr>';
        return;
    }

    document.getElementById('history-page').style.display = 'block';
    document.getElementById('user-page').style.display = 'none';
    document.getElementById('profileDropdown').classList.remove('active');
    // Fetch and render history when the page is shown
    fetchUserHistory();
    console.log('--- Exiting showHistoryPage ---');
}

// Call checkLoginStatusOnLoad when the script loads
checkLoginStatusOnLoad();

// Attach event listeners after defining functions
document.addEventListener('DOMContentLoaded', function() {
    const requestOtpBtn = document.getElementById('requestLoginOtp');
    if (requestOtpBtn) {
         requestOtpBtn.addEventListener('click', requestLoginOtp);
    }
    // Attach other event listeners here as needed...

    // Ensure initial visibility of login/profile based on state
    checkLoginStatusOnLoad(); // Call again to be safe after DOM is ready

    const verifyOtpBtn = document.getElementById('verifyLoginOtp');
    if (verifyOtpBtn) {
        verifyOtpBtn.addEventListener('click', function() {
            // Call the actual OTP verification function
            verifyLoginOtp();
        });
    }

});
