// Simple test for BOQ upload functionality
console.log('BOQ Upload Test Script Loaded');

// Test if the modal elements exist
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, testing BOQ upload elements...');
    
    // Check if modal exists
    const modal = document.getElementById('projectTypeModal');
    if (modal) {
        console.log('✓ Project Type Modal found');
    } else {
        console.log('✗ Project Type Modal not found');
    }
    
    // Check if BOQ upload zone exists
    const uploadZone = document.getElementById('boqUploadZone');
    if (uploadZone) {
        console.log('✓ BOQ Upload Zone found');
    } else {
        console.log('✗ BOQ Upload Zone not found');
    }
    
    // Check if file input exists
    const fileInput = document.getElementById('boqFileInput');
    if (fileInput) {
        console.log('✓ BOQ File Input found');
    } else {
        console.log('✗ BOQ File Input not found');
    }
    
    // Check if project type ID field exists
    const projectTypeId = document.getElementById('projectTypeId');
    if (projectTypeId) {
        console.log('✓ Project Type ID field found');
    } else {
        console.log('✗ Project Type ID field not found');
    }
    
    console.log('BOQ Upload Test Complete');
});
