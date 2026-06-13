/**
 * main.js — Frontend logic for phonecast
 * Handles drag-and-drop upload, forecast controls, table sorting, and CSV export.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // Flash message auto-dismiss
    // ============================================================
    document.querySelectorAll('.flash-message').forEach(function (msg) {
        // Auto dismiss after 6 seconds
        setTimeout(function () {
            msg.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(function () { msg.remove(); }, 300);
        }, 6000);

        // Close button
        var closeBtn = msg.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                msg.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(function () { msg.remove(); }, 300);
            });
        }
    });

    // ============================================================
    // Drag & Drop Upload
    // ============================================================
    var uploadZone = document.getElementById('upload-zone');
    var fileInput = document.getElementById('file-input');
    var browseBtn = document.getElementById('browse-btn');
    var analyzeBtn = document.getElementById('analyze-btn');
    var fileSelected = document.getElementById('file-selected');
    var fileName = document.getElementById('file-name');
    var uploadForm = document.getElementById('upload-form');
    var loadingOverlay = document.getElementById('loading-overlay');

    if (uploadZone && fileInput) {
        // Click to browse
        uploadZone.addEventListener('click', function (e) {
            if (e.target !== browseBtn && !browseBtn.contains(e.target)) {
                fileInput.click();
            }
        });

        if (browseBtn) {
            browseBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                fileInput.click();
            });
        }

        // Drag events
        ['dragenter', 'dragover'].forEach(function (evt) {
            uploadZone.addEventListener(evt, function (e) {
                e.preventDefault();
                e.stopPropagation();
                uploadZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(function (evt) {
            uploadZone.addEventListener(evt, function (e) {
                e.preventDefault();
                e.stopPropagation();
                uploadZone.classList.remove('dragover');
            });
        });

        uploadZone.addEventListener('drop', function (e) {
            var files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        });

        // File input change
        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                handleFileSelect(fileInput.files[0]);
            }
        });
    }

    function handleFileSelect(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showFlash('Please upload a .csv file. Other file formats are not supported.', 'error');
            fileInput.value = '';
            return;
        }

        if (fileName) fileName.textContent = file.name;
        if (fileSelected) fileSelected.classList.add('show');
        if (analyzeBtn) analyzeBtn.disabled = false;
    }

    // Upload form submit with loading spinner
    if (uploadForm) {
        uploadForm.addEventListener('submit', function () {
            if (loadingOverlay) {
                loadingOverlay.classList.add('show');
            }
        });
    }

    // ============================================================
    // Forecast Explorer Controls
    // ============================================================
    var forecastSlider = document.getElementById('forecast-slider');
    var forecastValue = document.getElementById('forecast-value');
    var brandCheckboxes = document.querySelectorAll('.brand-checkbox');
    var updateForecastBtn = document.getElementById('update-forecast');

    if (forecastSlider && forecastValue) {
        forecastSlider.addEventListener('input', function () {
            forecastValue.textContent = forecastSlider.value;
        });
    }

    if (updateForecastBtn) {
        updateForecastBtn.addEventListener('click', function () {
            updateForecast();
        });
    }

    function getSelectedBrands() {
        var selected = [];
        document.querySelectorAll('.brand-checkbox:checked').forEach(function (cb) {
            selected.push(cb.value);
        });
        return selected;
    }

    function updateForecast() {
        var quarters = forecastSlider ? parseInt(forecastSlider.value) : 4;
        var brands = getSelectedBrands();

        if (brands.length === 0) {
            showFlash('Please select at least one brand.', 'error');
            return;
        }

        // Show loading state on button
        if (updateForecastBtn) {
            updateForecastBtn.disabled = true;
            updateForecastBtn.innerHTML = '<i class="bi bi-arrow-repeat spin-icon"></i> Updating...';
        }

        fetch('/api/forecast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quarters: quarters, brands: brands })
        })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.error) {
                showFlash(data.error, 'error');
                return;
            }

            // Update chart
            var chartDiv = document.getElementById('forecast-chart');
            if (chartDiv && data.chart) {
                var chartData = JSON.parse(data.chart);
                Plotly.react(chartDiv, chartData.data, chartData.layout, { responsive: true });
            }

            // Update table
            updateForecastTable(data.periods, data.table, brands);
        })
        .catch(function (err) {
            showFlash('Error updating forecast: ' + err.message, 'error');
        })
        .finally(function () {
            if (updateForecastBtn) {
                updateForecastBtn.disabled = false;
                updateForecastBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Update Forecast';
            }
        });
    }

    function updateForecastTable(periods, tableData, brands) {
        var tbody = document.getElementById('forecast-table-body');
        var thead = document.getElementById('forecast-table-head');
        if (!tbody || !thead) return;

        // Update header
        var headerRow = '<th>Period</th>';
        brands.forEach(function (brand) {
            headerRow += '<th>' + brand + '</th>';
        });
        thead.innerHTML = '<tr>' + headerRow + '</tr>';

        // Update body
        var bodyHtml = '';
        periods.forEach(function (period) {
            bodyHtml += '<tr><td><strong>' + period + '</strong></td>';
            brands.forEach(function (brand) {
                var value = tableData[brand] && tableData[brand][period]
                    ? tableData[brand][period].toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})
                    : '—';
                bodyHtml += '<td>' + value + '</td>';
            });
            bodyHtml += '</tr>';
        });
        tbody.innerHTML = bodyHtml;
    }

    // ============================================================
    // Export Forecast CSV
    // ============================================================
    var exportForecastBtn = document.getElementById('export-forecast-csv');
    if (exportForecastBtn) {
        exportForecastBtn.addEventListener('click', function () {
            var quarters = forecastSlider ? parseInt(forecastSlider.value) : 4;
            var brands = getSelectedBrands();

            fetch('/download/forecast-csv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quarters: quarters, brands: brands })
            })
            .then(function (response) { return response.blob(); })
            .then(function (blob) {
                var url = window.URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'phonecast_forecast.csv';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch(function (err) {
                showFlash('Error exporting CSV: ' + err.message, 'error');
            });
        });
    }

    // ============================================================
    // Table Sorting
    // ============================================================
    document.querySelectorAll('.pc-table.sortable thead th').forEach(function (th) {
        th.addEventListener('click', function () {
            var table = th.closest('table');
            var tbody = table.querySelector('tbody');
            var rows = Array.from(tbody.querySelectorAll('tr'));
            var colIdx = Array.from(th.parentNode.children).indexOf(th);
            var isAsc = th.classList.contains('sort-asc');

            // Reset all headers
            table.querySelectorAll('th').forEach(function (h) {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            // Sort
            rows.sort(function (a, b) {
                var aVal = a.children[colIdx].textContent.trim();
                var bVal = b.children[colIdx].textContent.trim();

                // Try numeric
                var aNum = parseFloat(aVal.replace(/[%,]/g, ''));
                var bNum = parseFloat(bVal.replace(/[%,]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAsc ? bNum - aNum : aNum - bNum;
                }
                return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
            });

            th.classList.add(isAsc ? 'sort-desc' : 'sort-asc');

            rows.forEach(function (row) { tbody.appendChild(row); });
        });
    });

    // ============================================================
    // Plotly Chart Rendering Helper
    // ============================================================
    window.renderPlotlyChart = function (divId, chartJson) {
        if (!chartJson) return;
        var chartDiv = document.getElementById(divId);
        if (!chartDiv) return;

        try {
            var data = JSON.parse(chartJson);
            Plotly.newPlot(chartDiv, data.data, data.layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                displaylogo: false
            });
        } catch (e) {
            console.error('Error rendering chart:', divId, e);
        }
    };

    // ============================================================
    // Flash Message Helper
    // ============================================================
    function showFlash(message, type) {
        var container = document.querySelector('.flash-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'flash-container';
            document.body.appendChild(container);
        }

        var icon = type === 'error' ? 'bi-exclamation-circle' : 'bi-check-circle';
        var msg = document.createElement('div');
        msg.className = 'flash-message ' + type;
        msg.innerHTML = '<i class="bi ' + icon + '"></i> ' + message +
            ' <button class="close-btn">&times;</button>';

        container.appendChild(msg);

        msg.querySelector('.close-btn').addEventListener('click', function () {
            msg.remove();
        });

        setTimeout(function () {
            msg.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(function () { msg.remove(); }, 300);
        }, 6000);
    }

    // Add slideOut animation
    var style = document.createElement('style');
    style.textContent = '@keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } } .spin-icon { animation: spin 0.8s linear infinite; }';
    document.head.appendChild(style);

    // ============================================================
    // Select All / Deselect All for brand checkboxes
    // ============================================================
    var selectAllBtn = document.getElementById('select-all-brands');
    var deselectAllBtn = document.getElementById('deselect-all-brands');

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function () {
            document.querySelectorAll('.brand-checkbox').forEach(function (cb) {
                cb.checked = true;
            });
        });
    }

    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', function () {
            document.querySelectorAll('.brand-checkbox').forEach(function (cb) {
                cb.checked = false;
            });
        });
    }
});
