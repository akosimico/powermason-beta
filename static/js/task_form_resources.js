// Task Form Resource Management
// Handles dynamic form addition, deletion, and auto-filling

(function() {
    'use strict';

    let initialized = false;

    function init() {
        if (initialized) return;
        initialized = true;

        setupMaterialForms();
        setupEquipmentForms();
        setupManpowerForms();
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ========================================
    // MATERIAL FORMS
    // ========================================
    function setupMaterialForms() {
        const addBtn = document.getElementById('add-material-btn');
        const formContainer = document.getElementById('material-forms');

        if (!addBtn || !formContainer) return;

        // Remove any existing listeners by cloning the button
        const newAddBtn = addBtn.cloneNode(true);
        addBtn.parentNode.replaceChild(newAddBtn, addBtn);

        // Add single event listener
        newAddBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            addMaterialForm();
        }, {once: false});

        // Setup existing forms
        setupExistingMaterialRows();
    }

    function setupExistingMaterialRows() {
        document.querySelectorAll('.material-form-row').forEach(row => {
            setupMaterialRow(row);
            addDeleteButton(row, 'material');
        });
    }

    function addMaterialForm() {
        const formContainer = document.getElementById('material-forms');
        const totalForms = document.querySelector('#id_materials-TOTAL_FORMS');
        const formCount = parseInt(totalForms.value);

        // Get the first form as template (cleaner than last)
        const templateForm = formContainer.querySelector('.material-form-row:first-child');
        if (!templateForm) {
            console.error('No template form found');
            return;
        }

        const newForm = templateForm.cloneNode(true);

        // Update all name and id attributes
        updateFormIndexes(newForm, 'materials', formCount);

        // Clear all values
        clearFormValues(newForm);

        // Remove any existing delete buttons
        const existingDeleteBtn = newForm.querySelector('.delete-form-btn');
        if (existingDeleteBtn) {
            existingDeleteBtn.remove();
        }

        // Append new form
        formContainer.appendChild(newForm);

        // Setup the new form
        setupMaterialRow(newForm);

        // Update total forms count
        totalForms.value = formCount + 1;

        // Refresh delete buttons for all forms
        refreshDeleteButtons('materials');
    }

    function setupMaterialRow(row) {
        const materialSelect = row.querySelector('[name*="-material"]');
        const unitCostInput = row.querySelector('[name*="-unit_cost"]');

        if (!materialSelect || !unitCostInput) return;

        // Remove old event listeners by cloning
        const newMaterialSelect = materialSelect.cloneNode(true);
        // Preserve the selected value
        newMaterialSelect.value = materialSelect.value;
        materialSelect.parentNode.replaceChild(newMaterialSelect, materialSelect);

        // Add event listener for auto-fill
        newMaterialSelect.addEventListener('change', async function() {
            const materialId = this.value;
            if (!materialId) return;

            // Try to get price from data attribute first (faster)
            const priceAttr = this.getAttribute(`data-material-${materialId}`);
            if (priceAttr) {
                unitCostInput.value = parseFloat(priceAttr).toFixed(2);
                return;
            }

            // Fallback to API call
            try {
                const response = await fetch(`/materials_equipment/api/materials/${materialId}/`);
                if (response.ok) {
                    const data = await response.json();
                    // Auto-fill with standard price
                    if (data.standard_price) {
                        unitCostInput.value = parseFloat(data.standard_price).toFixed(2);
                    }
                }
            } catch (error) {
                console.error('Error fetching material data:', error);
            }
        });

        // Trigger change if material is already selected (for initial load)
        if (newMaterialSelect.value) {
            newMaterialSelect.dispatchEvent(new Event('change'));
        }
    }

    // ========================================
    // EQUIPMENT FORMS
    // ========================================
    function setupEquipmentForms() {
        const addBtn = document.getElementById('add-equipment-btn');
        const formContainer = document.getElementById('equipment-forms');

        if (!addBtn || !formContainer) return;

        // Remove any existing listeners
        const newAddBtn = addBtn.cloneNode(true);
        addBtn.parentNode.replaceChild(newAddBtn, addBtn);

        newAddBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            addEquipmentForm();
        }, {once: false});

        // Setup existing forms
        setupExistingEquipmentRows();
    }

    function setupExistingEquipmentRows() {
        document.querySelectorAll('.equipment-form-row').forEach(row => {
            setupEquipmentRow(row);
            addDeleteButton(row, 'equipment');
        });
    }

    function addEquipmentForm() {
        const formContainer = document.getElementById('equipment-forms');
        const totalForms = document.querySelector('#id_equipment-TOTAL_FORMS');
        const formCount = parseInt(totalForms.value);

        const templateForm = formContainer.querySelector('.equipment-form-row:first-child');
        if (!templateForm) {
            console.error('No template form found');
            return;
        }

        const newForm = templateForm.cloneNode(true);
        updateFormIndexes(newForm, 'equipment', formCount);
        clearFormValues(newForm);

        const existingDeleteBtn = newForm.querySelector('.delete-form-btn');
        if (existingDeleteBtn) {
            existingDeleteBtn.remove();
        }

        formContainer.appendChild(newForm);
        setupEquipmentRow(newForm);
        totalForms.value = formCount + 1;

        // Refresh delete buttons for all forms
        refreshDeleteButtons('equipment');
    }

    function setupEquipmentRow(row) {
        const equipmentSelect = row.querySelector('[name*="-equipment"]');
        const typeSelect = row.querySelector('[name*="-allocation_type"]');
        const dailyRateInput = row.querySelector('[name*="-daily_rate"]');
        const dailyRateContainer = dailyRateInput ? dailyRateInput.closest('.col-span-2') : null;

        if (!equipmentSelect) return;

        // Store data attributes before cloning
        const dataAttrs = {};
        Array.from(equipmentSelect.attributes).forEach(attr => {
            if (attr.name.startsWith('data-equipment-')) {
                dataAttrs[attr.name] = attr.value;
            }
        });

        // Clone to remove old listeners
        const newEquipmentSelect = equipmentSelect.cloneNode(true);
        newEquipmentSelect.value = equipmentSelect.value;

        // Restore data attributes
        Object.keys(dataAttrs).forEach(key => {
            newEquipmentSelect.setAttribute(key, dataAttrs[key]);
        });

        equipmentSelect.parentNode.replaceChild(newEquipmentSelect, equipmentSelect);

        // Auto-fill equipment type and rate
        newEquipmentSelect.addEventListener('change', async function() {
            const equipmentId = this.value;
            if (!equipmentId) return;

            // Try to get data from attributes first (faster)
            const ownershipType = this.getAttribute(`data-equipment-${equipmentId}-type`);
            const rentalRate = this.getAttribute(`data-equipment-${equipmentId}-rate`);

            if (ownershipType && typeSelect) {
                if (ownershipType === 'OWN') {
                    typeSelect.value = 'OWNED';
                    if (dailyRateInput) {
                        dailyRateInput.value = '0.00';
                        if (dailyRateContainer) {
                            dailyRateContainer.style.opacity = '0.6';
                            dailyRateInput.placeholder = 'Owned (no rental cost)';
                        }
                    }
                } else if (ownershipType === 'RNT') {
                    typeSelect.value = 'RENTAL';
                    if (dailyRateInput && rentalRate) {
                        dailyRateInput.value = parseFloat(rentalRate).toFixed(2);
                        if (dailyRateContainer) {
                            dailyRateContainer.style.opacity = '1';
                            dailyRateInput.placeholder = 'Daily Rate';
                        }
                    }
                }
                return;
            }

            // Fallback to API call
            try {
                const response = await fetch(`/materials_equipment/api/equipment/${equipmentId}/`);
                if (response.ok) {
                    const data = await response.json();

                    if (typeSelect) {
                        if (data.ownership_type_code === 'OWN') {
                            typeSelect.value = 'OWNED';
                            if (dailyRateInput) {
                                dailyRateInput.value = '0.00';
                                if (dailyRateContainer) {
                                    dailyRateContainer.style.opacity = '0.6';
                                    dailyRateInput.placeholder = 'Owned (no rental cost)';
                                }
                            }
                        } else if (data.ownership_type_code === 'RNT') {
                            typeSelect.value = 'RENTAL';
                            if (dailyRateInput && data.rental_rate) {
                                dailyRateInput.value = parseFloat(data.rental_rate).toFixed(2);
                                if (dailyRateContainer) {
                                    dailyRateContainer.style.opacity = '1';
                                    dailyRateInput.placeholder = 'Daily Rate';
                                }
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error fetching equipment data:', error);
            }
        });

        // Handle type changes
        if (typeSelect && dailyRateInput && dailyRateContainer) {
            const newTypeSelect = typeSelect.cloneNode(true);
            newTypeSelect.value = typeSelect.value;
            typeSelect.parentNode.replaceChild(newTypeSelect, typeSelect);

            newTypeSelect.addEventListener('change', function() {
                if (this.value === 'OWNED') {
                    dailyRateContainer.style.opacity = '0.6';
                    dailyRateInput.placeholder = 'Owned (no rental cost)';
                    if (!dailyRateInput.value || parseFloat(dailyRateInput.value) === 0) {
                        dailyRateInput.value = '0.00';
                    }
                } else {
                    dailyRateContainer.style.opacity = '1';
                    dailyRateInput.placeholder = 'Daily Rate';
                }
            });

            // Initialize state
            newTypeSelect.dispatchEvent(new Event('change'));
        }

        // Trigger change if equipment is already selected (for initial load)
        if (newEquipmentSelect.value) {
            newEquipmentSelect.dispatchEvent(new Event('change'));
        }
    }

    // ========================================
    // MANPOWER FORMS
    // ========================================
    function setupManpowerForms() {
        const addBtn = document.getElementById('add-manpower-btn');
        const formContainer = document.getElementById('manpower-forms');

        if (!addBtn || !formContainer) return;

        const projectManpowerLimit = parseInt(document.querySelector('[data-project-manpower]')?.dataset.projectManpower || 0);

        // Remove any existing listeners
        const newAddBtn = addBtn.cloneNode(true);
        addBtn.parentNode.replaceChild(newAddBtn, addBtn);

        newAddBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            addManpowerForm();
        }, {once: false});

        // Setup existing forms
        setupExistingManpowerRows(projectManpowerLimit);
    }

    function setupExistingManpowerRows(projectManpowerLimit) {
        document.querySelectorAll('.manpower-form-row').forEach(row => {
            setupManpowerRow(row, projectManpowerLimit);
            addDeleteButton(row, 'manpower');
        });
    }

    function addManpowerForm() {
        const formContainer = document.getElementById('manpower-forms');
        const totalForms = document.querySelector('#id_manpower-TOTAL_FORMS');
        const formCount = parseInt(totalForms.value);

        const templateForm = formContainer.querySelector('.manpower-form-row:first-child');
        if (!templateForm) {
            console.error('No template form found');
            return;
        }

        const newForm = templateForm.cloneNode(true);
        updateFormIndexes(newForm, 'manpower', formCount);
        clearFormValues(newForm);

        const existingDeleteBtn = newForm.querySelector('.delete-form-btn');
        if (existingDeleteBtn) {
            existingDeleteBtn.remove();
        }

        formContainer.appendChild(newForm);

        const projectManpowerLimit = parseInt(document.querySelector('[data-project-manpower]')?.dataset.projectManpower || 0);
        setupManpowerRow(newForm, projectManpowerLimit);

        totalForms.value = formCount + 1;

        // Refresh delete buttons for all forms
        refreshDeleteButtons('manpower');
    }

    function setupManpowerRow(row, projectManpowerLimit) {
        const workersInput = row.querySelector('[name*="-number_of_workers"]');
        if (!workersInput) return;

        // Clone to remove old listeners
        const newWorkersInput = workersInput.cloneNode(true);
        newWorkersInput.value = workersInput.value;
        workersInput.parentNode.replaceChild(newWorkersInput, workersInput);

        // Add info text
        addManpowerInfo(row, projectManpowerLimit);

        // Validation
        newWorkersInput.addEventListener('input', function() {
            validateManpower(row, projectManpowerLimit);
        });

        // Initial validation
        validateManpower(row, projectManpowerLimit);
    }

    function addManpowerInfo(row, projectManpowerLimit) {
        const workersInput = row.querySelector('[name*="-number_of_workers"]');
        if (!workersInput || !projectManpowerLimit) return;

        // Remove existing info
        const existingInfo = row.querySelector('.manpower-project-info');
        if (existingInfo) existingInfo.remove();

        const info = document.createElement('div');
        info.className = 'manpower-project-info text-xs text-gray-600 mt-1';
        info.textContent = `Project has ${projectManpowerLimit} worker${projectManpowerLimit !== 1 ? 's' : ''} assigned`;
        workersInput.parentElement.appendChild(info);
    }

    function validateManpower(row, projectManpowerLimit) {
        if (!projectManpowerLimit) return;

        const workersInput = row.querySelector('[name*="-number_of_workers"]');
        if (!workersInput) return;

        const currentValue = parseInt(workersInput.value) || 0;

        // Calculate total
        let totalWorkers = 0;
        document.querySelectorAll('.manpower-form-row').forEach(formRow => {
            const input = formRow.querySelector('[name*="-number_of_workers"]');
            const deleteCheckbox = formRow.querySelector('[name*="-DELETE"]');
            if (input && (!deleteCheckbox || !deleteCheckbox.checked)) {
                totalWorkers += parseInt(input.value) || 0;
            }
        });

        // Remove existing warnings
        const existingWarning = row.querySelector('.manpower-warning');
        if (existingWarning) existingWarning.remove();

        if (totalWorkers > projectManpowerLimit) {
            workersInput.classList.add('border-red-500', 'bg-red-50');
            const warning = document.createElement('div');
            warning.className = 'manpower-warning text-xs text-red-600 mt-1 font-medium';
            warning.textContent = `⚠ Total workers (${totalWorkers}) exceeds project limit (${projectManpowerLimit})`;
            workersInput.parentElement.appendChild(warning);
        } else {
            workersInput.classList.remove('border-red-500', 'bg-red-50');
            const available = projectManpowerLimit - totalWorkers;
            if (available >= 0) {
                const info = document.createElement('div');
                info.className = 'manpower-warning text-xs text-green-600 mt-1';
                info.textContent = `✓ ${available} worker${available !== 1 ? 's' : ''} remaining`;
                workersInput.parentElement.appendChild(info);
            }
        }
    }

    // ========================================
    // HELPER FUNCTIONS
    // ========================================
    function updateFormIndexes(form, prefix, newIndex) {
        // Update all form field names and IDs
        form.querySelectorAll('input, select, textarea').forEach(field => {
            if (field.name) {
                field.name = field.name.replace(new RegExp(`${prefix}-(\\d+)-`), `${prefix}-${newIndex}-`);
            }
            if (field.id) {
                field.id = field.id.replace(new RegExp(`id_${prefix}-(\\d+)-`), `id_${prefix}-${newIndex}-`);
            }
        });

        // Update labels
        form.querySelectorAll('label').forEach(label => {
            if (label.htmlFor) {
                label.htmlFor = label.htmlFor.replace(new RegExp(`id_${prefix}-(\\d+)-`), `id_${prefix}-${newIndex}-`);
            }
        });
    }

    function clearFormValues(form) {
        form.querySelectorAll('input, select, textarea').forEach(field => {
            if (field.type === 'checkbox') {
                field.checked = false;
            } else if (field.type === 'hidden') {
                // Clear ID fields only
                if (field.name && field.name.includes('-id')) {
                    field.value = '';
                }
            } else {
                field.value = '';
            }
        });
    }

    // ========================================
    // DELETE BUTTON FUNCTIONALITY
    // ========================================
    function addDeleteButton(formRow, formType) {
        // Check if delete button already exists
        if (formRow.querySelector('.delete-form-btn')) return;

        // Find the delete column
        const deleteCol = formRow.querySelector('.col-span-1:last-child');
        if (!deleteCol) return;

        // Count total forms (excluding those marked for deletion)
        const container = formRow.parentElement;
        const totalForms = container.querySelectorAll(`.${formType}-form-row`).length;

        // Don't show delete button if there's only 1 form
        if (totalForms <= 1) {
            deleteCol.innerHTML = '';
            return;
        }

        // Clear existing content
        deleteCol.innerHTML = '';

        // Create delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'delete-form-btn w-full h-10 flex items-center justify-center text-red-600 hover:text-white hover:bg-red-600 rounded-lg transition-colors border border-red-300';
        deleteBtn.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        `;
        deleteBtn.title = 'Remove this form';

        deleteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleDelete(formRow, formType, deleteBtn);
        });

        deleteCol.appendChild(deleteBtn);
    }

    function refreshDeleteButtons(formType) {
        // Refresh delete buttons for all forms of this type
        const container = document.getElementById(`${formType}-forms`);
        if (!container) return;

        const forms = container.querySelectorAll(`.${formType}-form-row`);
        forms.forEach(form => {
            // Remove existing delete button
            const existingBtn = form.querySelector('.delete-form-btn');
            if (existingBtn) {
                existingBtn.remove();
            }
            // Add button again (will check if it should be shown)
            addDeleteButton(form, formType);
        });
    }

    function handleDelete(formRow, formType, deleteBtn) {
        const idInput = formRow.querySelector('[name*="-id"]');
        const deleteCheckbox = formRow.querySelector('[name*="-DELETE"]');

        if (idInput && idInput.value) {
            // Existing form - mark for deletion
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
            }
            formRow.style.opacity = '0.5';
            formRow.style.pointerEvents = 'none';
            deleteBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
            `;
            deleteBtn.title = 'Undo delete';
            deleteBtn.style.pointerEvents = 'auto';

            // Change click handler to undo
            const newBtn = deleteBtn.cloneNode(true);
            deleteBtn.parentNode.replaceChild(newBtn, deleteBtn);
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (deleteCheckbox) {
                    deleteCheckbox.checked = false;
                }
                formRow.style.opacity = '1';
                formRow.style.pointerEvents = 'auto';
                // Restore original delete button
                const restoredBtn = newBtn.cloneNode(false);
                restoredBtn.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                `;
                restoredBtn.title = 'Remove this form';
                newBtn.parentNode.replaceChild(restoredBtn, newBtn);
                restoredBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDelete(formRow, formType, restoredBtn);
                });
            });
        } else {
            // New form - just remove it
            const container = formRow.parentNode;
            formRow.remove();

            // Update form count
            const totalForms = document.querySelector(`#id_${formType}-TOTAL_FORMS`);
            if (totalForms) {
                const newCount = parseInt(totalForms.value) - 1;
                totalForms.value = Math.max(1, newCount); // Keep at least 1

                // Reindex remaining forms
                const remainingForms = container.querySelectorAll(`.${formType}-form-row`);
                remainingForms.forEach((form, index) => {
                    updateFormIndexes(form, formType, index);
                });

                // Refresh delete buttons after removal
                refreshDeleteButtons(formType);
            }
        }
    }

})();
