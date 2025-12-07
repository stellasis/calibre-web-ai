/**
 * AI Search JavaScript Module
 * Handles AI search mode toggle and enhanced search functionality.
 */

(function($) {
    'use strict';

    // AI Search Module
    var AISearch = {
        
        /**
         * Initialize AI search functionality
         */
        init: function() {
            this.bindEvents();
            this.initTooltips();
        },

        /**
         * Bind event handlers
         */
        bindEvents: function() {
            // Handle search mode toggle with keyboard
            $('.ai-search-toggle .btn').on('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    window.location.href = $(this).attr('href');
                }
            });

            // Handle search form submission with AI mode
            $('form[role="search"]').on('submit', function(e) {
                var $form = $(this);
                var isAIMode = AISearch.isAISearchActive();
                
                if (isAIMode) {
                    // Add ai=1 parameter for AI search
                    var $aiInput = $form.find('input[name="ai"]');
                    if ($aiInput.length === 0) {
                        $form.append('<input type="hidden" name="ai" value="1">');
                    }
                }
            });
        },

        /**
         * Initialize Bootstrap tooltips
         */
        initTooltips: function() {
            $('.ai-search-toggle [data-toggle="tooltip"]').tooltip();
        },

        /**
         * Check if AI search mode is active
         * @returns {boolean}
         */
        isAISearchActive: function() {
            var urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('ai') === '1';
        },

        /**
         * Toggle between standard and AI search
         * @param {boolean} useAI - Whether to use AI search
         */
        toggleSearchMode: function(useAI) {
            var url = new URL(window.location.href);
            
            if (useAI) {
                url.searchParams.set('ai', '1');
            } else {
                url.searchParams.delete('ai');
            }
            
            window.location.href = url.toString();
        },

        /**
         * Get current search query
         * @returns {string}
         */
        getSearchQuery: function() {
            var urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('query') || '';
        }
    };

    // Initialize when DOM is ready
    $(document).ready(function() {
        AISearch.init();
    });

    // Expose module globally
    window.AISearch = AISearch;

})(jQuery);

