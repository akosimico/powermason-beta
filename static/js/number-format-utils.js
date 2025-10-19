/**
 * Number Formatting Utilities for PowerMason
 * Provides consistent number formatting across all templates
 */

/**
 * Format currency with peso sign and thousand separators
 * @param {number} amount - The amount to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted currency string
 * @example formatCurrency(1234567.89) // Returns "1,234,567.89"
 */
function formatCurrency(amount, decimals = 2) {
    if (amount === null || amount === undefined || isNaN(amount)) {
        return '0.00';
    }
    return Number(amount).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format currency with peso sign
 * @param {number} amount - The amount to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted currency string with peso sign
 * @example formatPeso(1234567.89) // Returns "₱1,234,567.89"
 */
function formatPeso(amount, decimals = 2) {
    return '₱' + formatCurrency(amount, decimals);
}

/**
 * Format number with thousand separators (no currency sign)
 * @param {number} number - The number to format
 * @param {number} decimals - Number of decimal places (default: 0)
 * @returns {string} Formatted number string
 * @example formatNumber(1234567) // Returns "1,234,567"
 */
function formatNumber(number, decimals = 0) {
    if (number === null || number === undefined || isNaN(number)) {
        return '0';
    }
    return Number(number).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format percentage
 * @param {number} percentage - The percentage to format
 * @param {number} decimals - Number of decimal places (default: 1)
 * @param {boolean} showSign - Whether to show + for positive numbers (default: true)
 * @returns {string} Formatted percentage string
 * @example formatPercentage(5.234, 1, true) // Returns "+5.2%"
 * @example formatPercentage(-3.5) // Returns "-3.5%"
 */
function formatPercentage(percentage, decimals = 1, showSign = true) {
    if (percentage === null || percentage === undefined || isNaN(percentage)) {
        return '0.0%';
    }
    const formatted = Number(percentage).toFixed(decimals);
    const sign = (showSign && percentage > 0) ? '+' : '';
    return `${sign}${formatted}%`;
}

/**
 * Parse a formatted number string back to a number
 * @param {string} formattedNumber - The formatted number string
 * @returns {number} The parsed number
 * @example parseFormattedNumber("1,234,567.89") // Returns 1234567.89
 */
function parseFormattedNumber(formattedNumber) {
    if (typeof formattedNumber === 'number') {
        return formattedNumber;
    }
    // Remove currency symbols, commas, and spaces
    const cleaned = String(formattedNumber).replace(/[₱$,\s]/g, '');
    return parseFloat(cleaned) || 0;
}

/**
 * Format a large number with K, M, B suffixes
 * @param {number} number - The number to format
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted number with suffix
 * @example formatCompactNumber(1234567) // Returns "1.2M"
 * @example formatCompactNumber(1234) // Returns "1.2K"
 */
function formatCompactNumber(number, decimals = 1) {
    if (number === null || number === undefined || isNaN(number)) {
        return '0';
    }

    const absNumber = Math.abs(number);
    const sign = number < 0 ? '-' : '';

    if (absNumber >= 1000000000) {
        return sign + (absNumber / 1000000000).toFixed(decimals) + 'B';
    } else if (absNumber >= 1000000) {
        return sign + (absNumber / 1000000).toFixed(decimals) + 'M';
    } else if (absNumber >= 1000) {
        return sign + (absNumber / 1000).toFixed(decimals) + 'K';
    }
    return sign + absNumber.toFixed(decimals);
}

/**
 * Get color class based on percentage value
 * @param {number} percentage - The percentage value
 * @returns {string} Tailwind CSS color class
 */
function getPercentageColorClass(percentage) {
    if (percentage < 0) return 'text-green-600';
    if (percentage > 0) return 'text-red-600';
    return 'text-gray-600';
}

/**
 * Get badge color class based on value comparison
 * @param {number} actual - Actual value
 * @param {number} standard - Standard/expected value
 * @returns {string} Tailwind CSS badge color classes
 */
function getBadgeColorClass(actual, standard) {
    if (actual < standard) return 'bg-green-100 text-green-800';
    if (actual > standard) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
}
