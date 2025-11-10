"""
Debug view to test PDF generation dependencies on Render
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import sys
import os

@login_required
def pdf_debug_test(request):
    """
    Test page to check PDF generation capabilities
    Shows all system info without actually generating a PDF
    """

    debug_info = {
        'tests': [],
        'environment': {},
        'dependencies': {},
        'suggestions': []
    }

    # Test 1: Python version
    debug_info['environment']['Python Version'] = sys.version
    debug_info['tests'].append({
        'name': 'Python Version',
        'status': '✓ Pass',
        'details': sys.version
    })

    # Test 2: Django
    try:
        import django
        debug_info['environment']['Django Version'] = django.get_version()
        debug_info['tests'].append({
            'name': 'Django',
            'status': '✓ Installed',
            'details': f'Version {django.get_version()}'
        })
    except ImportError as e:
        debug_info['tests'].append({
            'name': 'Django',
            'status': '✗ Error',
            'details': str(e)
        })

    # Test 3: WeasyPrint
    try:
        import weasyprint
        version = weasyprint.__version__ if hasattr(weasyprint, '__version__') else 'Unknown'
        debug_info['dependencies']['WeasyPrint'] = f'✓ Version {version}'
        debug_info['tests'].append({
            'name': 'WeasyPrint',
            'status': '✓ Installed',
            'details': f'Version {version}'
        })
    except ImportError as e:
        debug_info['dependencies']['WeasyPrint'] = f'✗ Not installed: {str(e)}'
        debug_info['tests'].append({
            'name': 'WeasyPrint',
            'status': '✗ Missing',
            'details': str(e)
        })
        debug_info['suggestions'].append('Run: pip install weasyprint')

    # Test 4: Cairo
    try:
        import cairocffi
        version = cairocffi.version if hasattr(cairocffi, 'version') else 'Unknown'
        debug_info['dependencies']['Cairo'] = f'✓ Version {version}'
        debug_info['tests'].append({
            'name': 'Cairo (cairocffi)',
            'status': '✓ Installed',
            'details': f'Version {version}'
        })
    except ImportError as e:
        debug_info['dependencies']['Cairo'] = f'✗ Not installed: {str(e)}'
        debug_info['tests'].append({
            'name': 'Cairo (cairocffi)',
            'status': '✗ Missing',
            'details': str(e)
        })
        debug_info['suggestions'].append('Install system package: libcairo2')

    # Test 5: Pango
    try:
        import pangocffi
        debug_info['dependencies']['Pango'] = '✓ Installed'
        debug_info['tests'].append({
            'name': 'Pango (pangocffi)',
            'status': '✓ Installed',
            'details': 'Available'
        })
    except ImportError as e:
        debug_info['dependencies']['Pango'] = f'✗ Not installed: {str(e)}'
        debug_info['tests'].append({
            'name': 'Pango (pangocffi)',
            'status': '✗ Missing',
            'details': str(e)
        })
        debug_info['suggestions'].append('Install system packages: libpango-1.0-0, libpangocairo-1.0-0')

    # Test 6: GDK-Pixbuf (Optional - only needed for SVG/WebP images)
    try:
        import gi
        gi.require_version('GdkPixbuf', '2.0')
        debug_info['dependencies']['GDK-Pixbuf'] = '✓ Installed'
        debug_info['tests'].append({
            'name': 'GDK-Pixbuf (Optional)',
            'status': '✓ Installed',
            'details': 'Available for SVG/WebP images'
        })
    except Exception as e:
        debug_info['dependencies']['GDK-Pixbuf'] = f'⚠ Not installed: {str(e)}'
        debug_info['tests'].append({
            'name': 'GDK-Pixbuf (Optional)',
            'status': '⚠ Missing',
            'details': 'Not required for basic PDF generation. Only needed for SVG/WebP images.'
        })
        # Don't add to suggestions since it's optional

    # Test 7: Fonts
    font_dirs = ['/usr/share/fonts', '/usr/local/share/fonts']
    font_count = 0
    found_fonts = []

    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            for root, dirs, files in os.walk(font_dir):
                for file in files:
                    if file.endswith(('.ttf', '.otf')):
                        font_count += 1
                        if len(found_fonts) < 10:  # Only show first 10
                            found_fonts.append(file)

    if font_count > 0:
        debug_info['dependencies']['Fonts'] = f'✓ {font_count} fonts found'
        debug_info['tests'].append({
            'name': 'System Fonts',
            'status': '✓ Available',
            'details': f'{font_count} fonts found. Examples: {", ".join(found_fonts[:5])}'
        })
    else:
        debug_info['dependencies']['Fonts'] = '✗ No fonts found'
        debug_info['tests'].append({
            'name': 'System Fonts',
            'status': '✗ Missing',
            'details': 'No TrueType or OpenType fonts found'
        })
        debug_info['suggestions'].append('Install fonts: fonts-liberation, fonts-dejavu')

    # Test 8: Try to create a simple PDF
    try:
        from weasyprint import HTML
        from io import BytesIO

        simple_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: DejaVu Sans, Arial, sans-serif; padding: 20px; }
                h1 { color: #2563eb; }
            </style>
        </head>
        <body>
            <h1>PDF Test</h1>
            <p>This is a test PDF generated on Render.</p>
            <p>If you can see this, PDF generation is working!</p>
        </body>
        </html>
        """

        # Create HTML object and render to PDF
        html_obj = HTML(string=simple_html)
        pdf_bytes = html_obj.write_pdf()

        if pdf_bytes and len(pdf_bytes) > 100:
            debug_info['tests'].append({
                'name': 'PDF Generation Test',
                'status': '✓ Success',
                'details': f'Generated {len(pdf_bytes):,} bytes PDF successfully'
            })
        else:
            debug_info['tests'].append({
                'name': 'PDF Generation Test',
                'status': '✗ Failed',
                'details': f'PDF too small: {len(pdf_bytes) if pdf_bytes else 0} bytes'
            })
            debug_info['suggestions'].append('PDF generation produced invalid output')

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        debug_info['tests'].append({
            'name': 'PDF Generation Test',
            'status': '✗ Error',
            'details': f'{str(e)}\n\nTraceback:\n{error_details}'
        })
        debug_info['suggestions'].append(f'PDF generation failed: {str(e)}')

    # Test 9: Template exists
    template_paths = [
        'templates/project_profiling/reports/weekly_cost_report_pdf.html',
        'templates/scheduling/weekly_progress/reports_pdf.html',
        'templates/debug/pdf_error.html'
    ]

    for template_path in template_paths:
        full_path = os.path.join(os.getcwd(), template_path)
        if os.path.exists(full_path):
            debug_info['tests'].append({
                'name': f'Template: {template_path.split("/")[-1]}',
                'status': '✓ Found',
                'details': full_path
            })
        else:
            debug_info['tests'].append({
                'name': f'Template: {template_path.split("/")[-1]}',
                'status': '✗ Missing',
                'details': f'Not found at {full_path}'
            })
            debug_info['suggestions'].append(f'Push template file: {template_path}')

    # Environment variables
    debug_info['environment']['RENDER'] = os.environ.get('RENDER', 'Not set (local)')
    debug_info['environment']['DEBUG'] = os.environ.get('DEBUG', 'Not set')
    debug_info['environment']['Working Directory'] = os.getcwd()

    # Count pass/fail
    total_tests = len(debug_info['tests'])
    passed_tests = len([t for t in debug_info['tests'] if '✓' in t['status']])
    failed_tests = total_tests - passed_tests

    debug_info['summary'] = {
        'total': total_tests,
        'passed': passed_tests,
        'failed': failed_tests,
        'status': 'Ready for PDF Generation' if failed_tests == 0 else 'Issues Found'
    }

    return render(request, 'debug/pdf_system_test.html', debug_info)
