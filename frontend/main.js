// =============================
// 1. Global State & Utilities
// =============================
let isLoggedIn = false;
let currentUser = null;
let userHistory = [];
let lastUploadedDailyAssessmentFileId = null;

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
        const res = await fetch('/api/daily-assessment/upload', {
            method: 'POST',
            body: fileData
        });
        if (!res.ok) throw new Error('Upload failed');
        alert('Daily Assessment file uploaded');

        // Add upload to history
        addHistoryEntry({
            date: new Date(),
            activity: 'DA File Upload',
            fileName: file.name,
            fileSize: file.size,
            fileId: fileId,
            reportId: '-'
        });

        const result = await res.json();
        console.log('Upload successful response:', result);
        alert('Daily Assessment file uploaded successfully!');

        // Store the uploaded file ID
        lastUploadedDailyAssessmentFileId = result.fileId;
        console.log('Stored last uploaded file ID:', lastUploadedDailyAssessmentFileId);

        // Send history entry to backend
        await fetch(`${BACKEND_URL}/api/history/`, {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({
                  user_id: currentUser.userId,
                 activity_type: 'Daily Assessment File Upload',
                 file_id: result.fileId,
                 file_name: file.name,
                  report_id: null,
                  filters: {}
             })
         });
         console.log('File upload history sent to backend.');

        return result.fileId;

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

async function generateReport() {
    if (!isLoggedIn || !currentUser) {
        showLoginPopup('Please login to generate report.');
        return;
    }

    // Use the last uploaded file ID
    const fileIdToAnalyze = lastUploadedDailyAssessmentFileId;

    if (!fileIdToAnalyze) {
        alert('Please upload a Daily Assessment file first.');
        return;
    }

    const reportId = generateUniqueId();
    const filters = getSelectedFilters('filter-form');

    console.log('Generating report with:', {
        userId: currentUser.userId,
        filters,
        reportId,
        fileId: fileIdToAnalyze
    });

    try {
        const res = await fetch(`${BACKEND_URL}/api/daily-assessment/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: currentUser.userId,
                filters,
                reportId,
                fileId: fileIdToAnalyze
            })
        });
        if (!res.ok) throw new Error('Failed to generate report');

        const result = await res.json();
        console.log('Report generation successful response:', result);

        // Add report generation to history
        await fetch(`${BACKEND_URL}/api/history/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.userId,
                activity_type: 'daily_assessment_report',
                file_id: fileIdToAnalyze,
                file_name: 'Daily_Assessment_Report',
                report_id: reportId,
                filters: filters
            })
        });
         console.log('Report history sent to backend.');

        alert(`Report generated successfully! Report ID: ${reportId}`);

        // Optionally, you could trigger a download here using result.reportPath
        // if your download endpoint is set up to serve files based on the path
        // window.open(`${BACKEND_URL}/api/daily-assessment/report/${reportId}`); // Assuming the GET endpoint works

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
        const res = await fetch('/api/impact-assessment/upload', {
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
        const res = await fetch('/api/impact-assessment/report', {
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

function requestLoginOtp() {
    const email = document.getElementById('loginEmail').value;

    if (!email || !email.endsWith('@agastya.org')) {
        alert('Please enter a valid @agastya.org email address');
        return;
    }

    console.log('OTP sent to:', email);
    document.getElementById('loginOtpContainer').classList.add('active');
    document.getElementById('requestLoginOtp').style.display = 'none';
    document.querySelector('#loginOtpContainer .otp-input[data-index="1"]').focus();
}

async function verifyLoginOtp() {
    let otp = '';
    document.querySelectorAll('#loginOtpContainer .otp-input').forEach(input => {
        otp += input.value;
    });

    const email = document.getElementById('loginEmail').value;

    if (otp === '1234') {
        const userId = generateUniqueIdForUser(email);

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp, userId })
            });

            const data = await res.json();

            loginUser({
                email: data.email,
                name: data.name,
                userId: data.userId,
                memberSince: data.memberSince || new Date().toDateString()
            });

            document.getElementById('login').style.display = 'none';
            document.getElementById('loginPopupOverlay').classList.add('show');
            document.getElementById('loginSuccessPopup').classList.add('show');

            document.getElementById('closeLoginPopup').addEventListener('click', () => {
                document.getElementById('loginPopupOverlay').classList.remove('show');
                document.getElementById('loginSuccessPopup').classList.remove('show');
                document.getElementById('home').scrollIntoView({ behavior: 'smooth' });
            });

            fetchUserHistory();

        } catch (error) {
            alert('Login failed. Please try again.');
        }

    } else {
        alert('Invalid OTP. Please try again.');
    }
}

function loginUser(user) {
    isLoggedIn = true;
    currentUser = user;

    // Update header UI
    document.getElementById('loginBtn').style.display = 'none';
    document.getElementById('userProfile').style.display = 'block';

    // Update user profile info
    document.getElementById('profileIcon').textContent = user.name.charAt(0).toUpperCase();
    document.getElementById('userName').textContent = user.name;
    document.getElementById('userEmail').textContent = user.email;
    document.getElementById('memberSince').textContent = user.memberSince;
    document.getElementById('profilePhoto').querySelector('span').textContent = user.name.charAt(0).toUpperCase();
}
