/**
 * Full Book Indexing JavaScript
 * Handles indexing UI interactions for Epic 6
 */

// Wait for jQuery to be available
(function() {
    'use strict';
    
    // Ensure jQuery is loaded before proceeding
    function initAIIndexing() {
        if (typeof jQuery === 'undefined' || typeof $ === 'undefined') {
            console.warn('AIIndexing: jQuery not available, retrying...');
            setTimeout(initAIIndexing, 100);
            return;
        }
        
        console.log('AIIndexing: jQuery available, initializing...');

    /**
     * Start indexing for a book
     */
    function startIndexing(bookId) {
        var url = '/api/ai/index/' + bookId;

        // Show loading state - hide both server-rendered and JS-rendered status
        $('#ai-index-loading').show();
        $('#ai-index-error').hide();
        $('#ai-index-status').hide();
        $('#ai-index-server-status').hide();
        $('#index-book-btn').prop('disabled', true);
        $('#force-reindex-btn').prop('disabled', true);
        $('#delete-index-btn').prop('disabled', true);

        // Make API call
        $.ajax({
            url: url,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('meta[name=csrf-token]').attr('content') || $('input[name=csrf_token]').val()
            },
            success: function(response) {
                console.log('Index API response:', JSON.stringify(response, null, 2));
                if (response.status === 'started') {
                    // Task queued, show loading with progress bar and poll for completion
                    $('#ai-index-loading').html(
                        '<div class="alert alert-info">' +
                        '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' + 
                        '<strong>Indexing started...</strong> Extracting and chunking book content.' +
                        '<div class="progress" style="margin-top: 10px; margin-bottom: 0;">' +
                        '<div class="progress-bar progress-bar-striped active" role="progressbar" ' +
                        'style="width: 5%">Starting...</div></div>' +
                        '</div>'
                    );
                    
                    // Poll for indexing completion
                    pollForIndexStatus(bookId, 0);
                } else if (response.status === 'already_indexed') {
                    // Already indexed
                    displayIndexStatus({
                        status: 'completed',
                        total_chunks: response.total_chunks,
                        processed_chunks: response.total_chunks
                    });
                } else if (response.status === 'in_progress') {
                    // Already in progress - show with progress bar
                    $('#ai-index-loading').html(
                        '<div class="alert alert-info">' +
                        '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' + 
                        '<strong>Indexing in progress...</strong>' +
                        '<div class="progress" style="margin-top: 10px; margin-bottom: 0;">' +
                        '<div class="progress-bar progress-bar-striped active" role="progressbar" ' +
                        'style="width: 10%">Processing...</div></div>' +
                        '</div>'
                    );
                    pollForIndexStatus(bookId, 0);
                } else {
                    showIndexError('Unexpected response from server');
                }
            },
            error: function(xhr) {
                var errorMsg = 'Failed to start indexing';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'AI features or full indexing is disabled';
                } else if (xhr.status === 404) {
                    errorMsg = 'Book not found';
                } else if (xhr.status === 401) {
                    errorMsg = 'Unauthorized. Please log in.';
                }
                showIndexError(errorMsg);
            }
        });
    }

    /**
     * Poll for indexing status
     */
    function pollForIndexStatus(bookId, attempt) {
        var maxAttempts = 300; // 5 minutes max (1 second intervals)
        if (attempt >= maxAttempts) {
            showIndexError('Indexing is taking longer than expected. Please refresh the page.');
            return;
        }

        $.ajax({
            url: '/api/ai/index/' + bookId + '/status',
            method: 'GET',
            success: function(response) {
                console.log('Index status response:', response);
                
                if (response.status === 'completed') {
                    displayIndexStatus(response);
                } else if (response.status === 'failed') {
                    showIndexError(response.error_message || 'Indexing failed');
                } else if (response.status === 'chunked_but_not_embedded') {
                    // Chunks exist but embeddings failed - show specific error
                    showIndexError('Embedding failed. Chunks: ' + response.chunk_count + ', Embeddings: ' + response.embedding_count + '. Please check AI configuration and try re-indexing.');
                } else if (response.status === 'partially_embedded') {
                    // Show partial progress with progress bar
                    var progress = response.embedding_count && response.chunk_count ? 
                        (response.embedding_count / response.chunk_count * 100) : 0;
                    $('#ai-index-loading').html(
                        '<div class="alert alert-info">' +
                        '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' + 
                        '<strong>Indexing in progress:</strong> ' + response.embedding_count + '/' + response.chunk_count + 
                        ' chunks embedded' +
                        '<div class="progress" style="margin-top: 10px; margin-bottom: 0;">' +
                        '<div class="progress-bar progress-bar-striped active" role="progressbar" ' +
                        'style="width: ' + progress + '%">' +
                        Math.round(progress) + '%' +
                        '</div></div>' +
                        '</div>'
                    );
                    // Continue polling
                    setTimeout(function() {
                        pollForIndexStatus(bookId, attempt + 1);
                    }, 1000);
                } else if (response.status === 'processing') {
                    // Check if stale (no update in 5+ minutes)
                    if (response.is_stale) {
                        // Show stale warning with resume button
                        $('#ai-index-loading').html(
                            '<div class="alert alert-warning">' +
                            '<span class="glyphicon glyphicon-exclamation-sign"></span> ' + 
                            '<strong>Task appears stuck</strong> - Last progress: ' + 
                            response.processed_chunks + '/' + response.total_chunks + ' chunks. ' +
                            'The indexing task may have crashed or timed out. ' +
                            '<br><br>' +
                            '<button class="btn btn-sm btn-primary" onclick="AIIndexing.startIndexing(' + bookId + ')">' +
                            '<span class="glyphicon glyphicon-repeat"></span> Resume Indexing</button>' +
                            '</div>'
                        );
                        // Stop polling - user needs to click resume
                        return;
                    }
                    
                    // Update progress
                    var progress = response.progress || 0;
                    $('#ai-index-loading').html(
                        '<div class="alert alert-info">' +
                        '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' +
                        'Indexing in progress: ' + response.processed_chunks + '/' + response.total_chunks +
                        ' chunks (' + progress.toFixed(1) + '%)' +
                        '<div class="progress" style="margin-top: 10px; margin-bottom: 10px;">' +
                        '<div class="progress-bar progress-bar-striped active" role="progressbar" ' +
                        'style="width: ' + progress + '%">' +
                        progress.toFixed(1) + '%' +
                        '</div></div>' +
                        '<button class="btn btn-xs btn-warning" onclick="AIIndexing.forceReindex(' + bookId + ')" style="margin-top: 5px;">' +
                        '<span class="glyphicon glyphicon-repeat"></span> Force Re-index</button>' +
                        '</div>'
                    );
                    
                    // Continue polling
                    setTimeout(function() {
                        pollForIndexStatus(bookId, attempt + 1);
                    }, 1000);
                } else if (response.status === 'stale') {
                    // Explicitly stale status from backend
                    $('#ai-index-loading').html(
                        '<div class="alert alert-warning">' +
                        '<span class="glyphicon glyphicon-exclamation-sign"></span> ' + 
                        '<strong>Task timed out</strong> - Progress: ' + 
                        response.embedding_count + '/' + response.chunk_count + ' chunks embedded. ' +
                        '<br><br>' +
                        '<button class="btn btn-sm btn-primary" onclick="AIIndexing.startIndexing(' + bookId + ')">' +
                        '<span class="glyphicon glyphicon-repeat"></span> Resume Indexing</button>' +
                        '</div>'
                    );
                } else if (response.status === 'pending' || response.status === 'queued') {
                    // Task queued but not started - show with progress bar
                    $('#ai-index-loading').html(
                        '<div class="alert alert-info">' +
                        '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' + 
                        '<strong>Queued...</strong> Waiting to start indexing.' +
                        '<div class="progress" style="margin-top: 10px; margin-bottom: 0;">' +
                        '<div class="progress-bar progress-bar-striped active" role="progressbar" ' +
                        'style="width: 2%">Queued</div></div>' +
                        '</div>'
                    );
                    setTimeout(function() {
                        pollForIndexStatus(bookId, attempt + 1);
                    }, 1000);
                } else {
                    // Unknown status - log and continue polling
                    console.warn('Unknown index status:', response.status);
                    setTimeout(function() {
                        pollForIndexStatus(bookId, attempt + 1);
                    }, 1000);
                }
            },
            error: function(xhr) {
                // On error, continue polling (might be temporary)
                setTimeout(function() {
                    pollForIndexStatus(bookId, attempt + 1);
                }, 2000);
            }
        });
    }

    /**
     * Display indexing status
     */
    function displayIndexStatus(statusData) {
        $('#ai-index-loading').hide();
        $('#ai-index-error').hide();

        // Update server-rendered status with completed message
        var chunks = statusData.total_chunks || statusData.chunk_count || 0;
        var statusHtml = '<span class="label label-success">' +
            '<span class="glyphicon glyphicon-ok"></span> ' +
            'Indexed (' + chunks + ' chunks)</span>';

        if (statusData.completed_at) {
            statusHtml += '<br><small>Completed: ' + new Date(statusData.completed_at).toLocaleString() + '</small>';
        }

        $('#ai-index-server-status').html(statusHtml).show();
        $('#ai-index-status').hide();

        // Show correct buttons for completed state
        $('#index-book-btn').hide();
        $('#delete-index-btn').show().prop('disabled', false);
        $('#force-reindex-btn').hide();

        // Show chatbot section now that indexing is complete
        $('#chatbot-not-indexed').hide();
        $('#chatbot-section').show();
    }

    /**
     * Show indexing error
     */
    function showIndexError(message) {
        $('#ai-index-loading').hide();
        $('#ai-index-error-message').text(message);
        $('#ai-index-error').show();
        $('#index-book-btn').prop('disabled', false);
    }

    /**
     * Force re-index for a book (resets status and restarts)
     */
    function forceReindex(bookId) {
        if (!confirm('Force re-index? This will reset the current indexing task and start fresh.')) {
            return;
        }

        // Reset the status first
        $.ajax({
            url: '/api/ai/index/' + bookId + '/reset',
            method: 'POST',
            headers: {
                'X-CSRFToken': $('meta[name=csrf-token]').attr('content') || $('input[name=csrf_token]').val()
            },
            success: function(response) {
                // Now start fresh
                startIndexing(bookId);
            },
            error: function(xhr) {
                // Even if reset fails, try to start anyway
                startIndexing(bookId);
            }
        });
    }

    /**
     * Delete index for a book
     */
    function deleteIndex(bookId) {
        if (!confirm('Are you sure you want to delete the index for this book? This cannot be undone.')) {
            return;
        }

        $.ajax({
            url: '/api/ai/index/' + bookId,
            method: 'DELETE',
            headers: {
                'X-CSRFToken': $('meta[name=csrf-token]').attr('content') || $('input[name=csrf_token]').val()
            },
            success: function(response) {
                if (response.status === 'deleted') {
                    // Reload page to refresh status
                    location.reload();
                }
            },
            error: function(xhr) {
                var errorMsg = 'Failed to delete index';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                alert(errorMsg);
            }
        });
    }

    /**
     * Search indexed content
     */
    function searchIndexedContent(query, bookId, limit) {
        limit = limit || 20;
        
        $.ajax({
            url: '/api/ai/index/search',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                query: query,
                book_id: bookId || null,
                limit: limit
            }),
            headers: {
                'X-CSRFToken': $('meta[name=csrf-token]').attr('content') || $('input[name=csrf_token]').val()
            },
            success: function(response) {
                displaySearchResults(response.results, response.query);
            },
            error: function(xhr) {
                var errorMsg = 'Search failed';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                alert(errorMsg);
            }
        });
    }

    /**
     * Display search results
     */
    function displaySearchResults(results, query) {
        var resultsHtml = '<h3>Search Results for: "' + query + '"</h3>';
        
        if (results.length === 0) {
            resultsHtml += '<div class="alert alert-info">No results found.</div>';
        } else {
            resultsHtml += '<div class="list-group">';
            results.forEach(function(result) {
                resultsHtml += 
                    '<div class="list-group-item">' +
                    '<h4 class="list-group-item-heading">' +
                    (result.book ? result.book.title : 'Book ' + result.book_id) +
                    (result.chapter_title ? ' - ' + result.chapter_title : '') +
                    '</h4>' +
                    '<p class="list-group-item-text">' +
                    result.chunk_text.substring(0, 300) + 
                    (result.chunk_text.length > 300 ? '...' : '') +
                    '</p>' +
                    '<small>Similarity: ' + (result.similarity_score * 100).toFixed(1) + '%</small>' +
                    '</div>';
            });
            resultsHtml += '</div>';
        }
        
        $('#chunk-search-results').html(resultsHtml).show();
    }

    /**
     * Load indexing statistics for admin dashboard
     */
    function loadIndexingStats() {
        console.log('AIIndexing: Loading stats from /api/ai/index/stats');
        $.ajax({
            url: '/api/ai/index/stats',
            method: 'GET',
            success: function(response) {
                console.log('AIIndexing: Stats loaded successfully', response);
                $('#indexing-stats-loading').hide();
                $('#indexing-stats-error').hide();
                $('#indexing-stats').show();
                
                $('#stats-indexed-books').text(response.indexed_books || 0);
                $('#stats-total-chunks').text(response.total_chunks || 0);
                $('#stats-storage').text(response.storage_estimate_mb || '0.00');
            },
            error: function(xhr, status, error) {
                console.error('AIIndexing: Failed to load stats', {
                    status: xhr.status,
                    statusText: xhr.statusText,
                    response: xhr.responseJSON || xhr.responseText,
                    error: error
                });
                $('#indexing-stats-loading').hide();
                $('#indexing-stats').hide();
                $('#indexing-stats-error').show();
                var errorMsg = 'Failed to load statistics';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'Full book indexing is disabled. Enable it in AI Settings.';
                } else if (xhr.status === 0) {
                    errorMsg = 'Network error. Please check your connection.';
                } else if (xhr.status >= 500) {
                    errorMsg = 'Server error. Please try again later.';
                } else if (xhr.status === 404) {
                    errorMsg = 'API endpoint not found. Please check the server configuration.';
                }
                $('#indexing-stats-error-message').text(errorMsg);
            }
        });
    }

    /**
     * Load indexing queue status for admin dashboard
     */
    function loadIndexingQueue() {
        $.ajax({
            url: '/api/ai/index/queue',
            method: 'GET',
            success: function(response) {
                $('#indexing-queue-loading').hide();
                $('#indexing-queue').show();
                
                if (response.tasks && response.tasks.length > 0) {
                    $('#queue-status-message').text(
                        'There are ' + response.count + ' indexing task(s) in the queue.'
                    );
                    
                    var tasksHtml = '';
                    response.tasks.forEach(function(task) {
                        var statusClass = task.status === 'processing' ? 'info' : 'default';
                        var statusIcon = task.status === 'processing' 
                            ? '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span>'
                            : '<span class="glyphicon glyphicon-time"></span>';
                        
                        tasksHtml += '<li class="list-group-item">' +
                            statusIcon + ' ' +
                            '<strong>Book ID ' + task.book_id + '</strong> - ' +
                            '<span class="label label-' + statusClass + '">' + task.status + '</span>' +
                            (task.message ? ' - ' + task.message : '') +
                            (task.progress > 0 ? ' (' + Math.round(task.progress * 100) + '%)' : '') +
                            '</li>';
                    });
                    $('#queue-tasks-list').html(tasksHtml);
                } else {
                    $('#queue-status-message').text('No indexing tasks in the queue.');
                    $('#queue-tasks-list').html('');
                }
            },
            error: function(xhr) {
                $('#indexing-queue-loading').hide();
                var errorMsg = 'Failed to load queue status.';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'Full book indexing is disabled. Enable it in AI Settings.';
                }
                $('#indexing-queue').html(
                    '<div class="alert alert-danger">' +
                    '<span class="glyphicon glyphicon-exclamation-sign"></span> ' +
                    errorMsg +
                    '</div>'
                );
                console.error('Failed to load indexing queue:', xhr.status, xhr.responseJSON || xhr.responseText);
            }
        });
    }

    /**
     * Bulk index all books
     */
    function bulkIndexAll() {
        if (!confirm('This will queue indexing for all books in your library. This may take a very long time. Continue?')) {
            return;
        }
        
        $('#bulk-index-status').show();
        $('#bulk-index-message').text('Queuing books for indexing...');
        $('#bulk-index-all-btn').prop('disabled', true);
        $('#bulk-index-unindexed-btn').prop('disabled', true);
        
        $.ajax({
            url: '/api/ai/index/bulk/all',
            method: 'POST',
            headers: {
                'X-CSRFToken': $('meta[name=csrf-token]').attr('content') || $('input[name=csrf_token]').val()
            },
            success: function(response) {
                $('#bulk-index-message').html(
                    '<strong>Success!</strong> ' + response.message + '<br>' +
                    'Total books: ' + response.total_books + '<br>' +
                    'Already indexed: ' + response.already_indexed + '<br>' +
                    'In progress: ' + response.in_progress + '<br>' +
                    'Queued: ' + response.queued_count
                );
                $('#bulk-index-status').removeClass('alert-info').addClass('alert-success');
                
                // Reload stats and queue
                setTimeout(function() {
                    loadIndexingStats();
                    loadIndexingQueue();
                }, 1000);
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON && xhr.responseJSON.error 
                    ? xhr.responseJSON.error 
                    : 'Failed to start bulk indexing';
                $('#bulk-index-message').html('<strong>Error:</strong> ' + errorMsg);
                $('#bulk-index-status').removeClass('alert-info').addClass('alert-danger');
            },
            complete: function() {
                $('#bulk-index-all-btn').prop('disabled', false);
                $('#bulk-index-unindexed-btn').prop('disabled', false);
            }
        });
    }

    /**
     * Bulk index unindexed books only
     */
    function bulkIndexUnindexed() {
        if (!confirm('This will queue indexing for all books that haven\'t been indexed yet. Continue?')) {
            return;
        }
        
        $('#bulk-index-status').show();
        $('#bulk-index-message').text('Queuing unindexed books for indexing...');
        $('#bulk-index-all-btn').prop('disabled', true);
        $('#bulk-index-unindexed-btn').prop('disabled', true);
        
        $.ajax({
            url: '/api/ai/index/bulk/unindexed',
            method: 'POST',
            headers: {
                'X-CSRFToken': $('meta[name=csrf-token]').attr('content') || $('input[name=csrf_token]').val()
            },
            success: function(response) {
                $('#bulk-index-message').html(
                    '<strong>Success!</strong> ' + response.message + '<br>' +
                    'Total books: ' + response.total_books + '<br>' +
                    'Already indexed: ' + response.already_indexed + '<br>' +
                    'Queued: ' + response.queued_count
                );
                $('#bulk-index-status').removeClass('alert-info').addClass('alert-success');
                
                // Reload stats and queue
                setTimeout(function() {
                    loadIndexingStats();
                    loadIndexingQueue();
                }, 1000);
            },
            error: function(xhr) {
                var errorMsg = xhr.responseJSON && xhr.responseJSON.error 
                    ? xhr.responseJSON.error 
                    : 'Failed to start bulk indexing';
                $('#bulk-index-message').html('<strong>Error:</strong> ' + errorMsg);
                $('#bulk-index-status').removeClass('alert-info').addClass('alert-danger');
            },
            complete: function() {
                $('#bulk-index-all-btn').prop('disabled', false);
                $('#bulk-index-unindexed-btn').prop('disabled', false);
            }
        });
    }

    // Export functions to global scope
    window.AIIndexing = {
        startIndexing: startIndexing,
        forceReindex: forceReindex,
        deleteIndex: deleteIndex,
        searchIndexedContent: searchIndexedContent,
        pollForIndexStatus: pollForIndexStatus,
        loadIndexingStats: loadIndexingStats,
        loadIndexingQueue: loadIndexingQueue,
        bulkIndexAll: bulkIndexAll,
        bulkIndexUnindexed: bulkIndexUnindexed
    };

    // Auto-initialize on page load if elements exist
    $(document).ready(function() {
        console.log('AIIndexing: Document ready, checking for UI elements...');

        // Check if we're on a book detail page with indexing UI
        // Look for any of the indexing buttons (they may have different IDs depending on status)
        var $indexBtn = $('#index-book-btn, #reindex-book-btn, #force-reindex-btn').first();
        if ($indexBtn.length > 0) {
            var bookId = $indexBtn.data('book-id');
            if (bookId) {
                // Check initial status
                $.ajax({
                    url: '/api/ai/index/' + bookId + '/status',
                    method: 'GET',
                    success: function(response) {
                        if (response.status === 'completed') {
                            displayIndexStatus(response);
                        } else if (response.status === 'processing' || response.status === 'stale') {
                            // Resume polling for processing or stale tasks
                            pollForIndexStatus(bookId, 0);
                        }
                    }
                });
            }
        }
        
        // Check if we're on admin page with indexing dashboard
        if ($('#indexing-stats').length > 0) {
            console.log('AIIndexing: Admin dashboard found, loading stats...');
            // Load stats and queue status
            loadIndexingStats();
            loadIndexingQueue();
            
            // Refresh queue every 10 seconds
            setInterval(function() {
                loadIndexingQueue();
            }, 10000);
            
            // Refresh stats every 30 seconds
            setInterval(function() {
                loadIndexingStats();
            }, 30000);
        } else {
            console.log('AIIndexing: Admin dashboard elements not found (checked for #indexing-stats)');
        }
    });
    
    } // End of initAIIndexing function
    
    // Start initialization - wait for jQuery
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAIIndexing);
    } else {
        // DOM already loaded, start immediately
        initAIIndexing();
    }
})();


