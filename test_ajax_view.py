from django.shortcuts import render
from django.http import HttpResponse

def test_ajax_navigation(request):
    """Test view for AJAX navigation components"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AJAX Navigation Test</title>
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Load Chart.js first -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <!-- Load the AJAX Navigation Scripts -->
    <script src="/static/js/module-initializer.js"></script>
    <script src="/static/js/materials-module.js"></script>
    <script src="/static/js/equipment-module.js"></script>
    <script src="/static/js/client_management.js"></script>
    <script src="/static/js/dashboard-complete.js"></script>
    <script src="/static/js/ajax-navigation.js"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-900 mb-8">AJAX Navigation Test</h1>
        
        <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">Test Results</h2>
            <div id="test-results" class="space-y-2">
                <div class="flex items-center space-x-2">
                    <div id="ajax-nav-test" class="w-4 h-4 bg-gray-300 rounded-full"></div>
                    <span>AJAX Navigation System</span>
                </div>
                <div class="flex items-center space-x-2">
                    <div id="module-init-test" class="w-4 h-4 bg-gray-300 rounded-full"></div>
                    <span>Module Initializer</span>
                </div>
                <div class="flex items-center space-x-2">
                    <div id="client-mgmt-test" class="w-4 h-4 bg-gray-300 rounded-full"></div>
                    <span>Client Management Module</span>
                </div>
                <div class="flex items-center space-x-2">
                    <div id="dashboard-test" class="w-4 h-4 bg-gray-300 rounded-full"></div>
                    <span>Dashboard Module</span>
                </div>
                <div class="flex items-center space-x-2">
                    <div id="materials-test" class="w-4 h-4 bg-gray-300 rounded-full"></div>
                    <span>Materials Module</span>
                </div>
                <div class="flex items-center space-x-2">
                    <div id="equipment-test" class="w-4 h-4 bg-gray-300 rounded-full"></div>
                    <span>Equipment Module</span>
                </div>
            </div>
        </div>
        
        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Console Output</h2>
            <div id="console-output" class="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm h-64 overflow-y-auto">
                <div>Loading test...</div>
            </div>
        </div>
        
        <div class="bg-white rounded-lg shadow-lg p-6 mt-6">
            <h2 class="text-xl font-semibold mb-4">Instructions</h2>
            <div class="space-y-2 text-sm text-gray-600">
                <p>1. If all components show green circles ✅, the AJAX navigation system is working correctly</p>
                <p>2. If any show red circles ❌, check the browser console for specific errors</p>
                <p>3. After testing, navigate to your main application to test actual AJAX navigation</p>
                <p>4. Click sidebar links to test seamless navigation between modules</p>
            </div>
        </div>
    </div>

    <script>
        // Test script to verify AJAX navigation components
        function runTests() {
            const results = {
                ajaxNav: false,
                moduleInit: false,
                clientMgmt: false,
                dashboard: false,
                materials: false,
                equipment: false
            };
            
            const consoleOutput = document.getElementById('console-output');
            
            function log(message) {
                consoleOutput.innerHTML += `<div>${new Date().toLocaleTimeString()}: ${message}</div>`;
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }
            
            // Test AJAX Navigation
            if (typeof window.ajaxNavigation !== 'undefined') {
                results.ajaxNav = true;
                document.getElementById('ajax-nav-test').className = 'w-4 h-4 bg-green-500 rounded-full';
                log('✅ AJAX Navigation system loaded');
            } else {
                document.getElementById('ajax-nav-test').className = 'w-4 h-4 bg-red-500 rounded-full';
                log('❌ AJAX Navigation system not found');
            }
            
            // Test Module Initializer
            if (typeof window.ModuleRegistry !== 'undefined') {
                results.moduleInit = true;
                document.getElementById('module-init-test').className = 'w-4 h-4 bg-green-500 rounded-full';
                log('✅ Module Initializer loaded');
            } else {
                document.getElementById('module-init-test').className = 'w-4 h-4 bg-red-500 rounded-full';
                log('❌ Module Initializer not found');
            }
            
            // Test Client Management
            if (typeof window.initializeClientManagement === 'function') {
                results.clientMgmt = true;
                document.getElementById('client-mgmt-test').className = 'w-4 h-4 bg-green-500 rounded-full';
                log('✅ Client Management module loaded');
            } else {
                document.getElementById('client-mgmt-test').className = 'w-4 h-4 bg-red-500 rounded-full';
                log('❌ Client Management module not found');
            }
            
            // Test Dashboard
            if (typeof window.initializeDashboard === 'function') {
                results.dashboard = true;
                document.getElementById('dashboard-test').className = 'w-4 h-4 bg-green-500 rounded-full';
                log('✅ Dashboard module loaded');
            } else {
                document.getElementById('dashboard-test').className = 'w-4 h-4 bg-red-500 rounded-full';
                log('❌ Dashboard module not found');
            }
            
            // Test Materials
            if (typeof window.initializeMaterials === 'function') {
                results.materials = true;
                document.getElementById('materials-test').className = 'w-4 h-4 bg-green-500 rounded-full';
                log('✅ Materials module loaded');
            } else {
                document.getElementById('materials-test').className = 'w-4 h-4 bg-red-500 rounded-full';
                log('❌ Materials module not found');
            }
            
            // Test Equipment
            if (typeof window.initializeEquipment === 'function') {
                results.equipment = true;
                document.getElementById('equipment-test').className = 'w-4 h-4 bg-green-500 rounded-full';
                log('✅ Equipment module loaded');
            } else {
                document.getElementById('equipment-test').className = 'w-4 h-4 bg-red-500 rounded-full';
                log('❌ Equipment module not found');
            }
            
            // Summary
            const passed = Object.values(results).filter(Boolean).length;
            const total = Object.keys(results).length;
            
            log(`\\n📊 Test Summary: ${passed}/${total} modules loaded successfully`);
            
            if (passed === total) {
                log('🎉 All AJAX navigation components are working correctly!');
                log('✅ You can now test actual navigation in your main application');
            } else {
                log('⚠️ Some components are missing. Check the file paths and script loading order.');
                log('💡 Make sure all JavaScript files are in the correct static directories');
            }
        }
        
        // Run tests after a short delay to allow scripts to load
        setTimeout(runTests, 1000);
    </script>
</body>
</html>
    """
    return HttpResponse(html_content)
