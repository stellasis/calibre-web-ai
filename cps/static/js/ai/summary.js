/**
 * AI Summary Generation JavaScript
 * Handles summary generation UI interactions
 */

(function() {
    'use strict';

    function generateSummary(bookId, regenerate) {
        var url = '/api/ai/summary/' + bookId;
        if (regenerate) {
            url += '?regenerate=1';
        }

        // Show loading state
        $('#ai-summary-loading').show();
        $('#ai-summary-error').hide();
        $('#ai-summary-display').hide();
        $('#generate-ai-summary').prop('disabled', true);

        // Make API call
        $.ajax({
            url: url,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('meta[name=csrf-token]').attr('content') || $('input[name=csrf_token]').val()
            },
            success: function(response) {
                if (response.status === 'queued') {
                    // Task queued, show loading and poll for completion
                    $('#ai-summary-loading').html(
                        '<div class="alert alert-info">' +
                        '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' + 
                        'Summary generation started. This may take a moment...' +
                        '</div>'
                    );
                    
                    // Poll for summary completion
                    pollForSummary(bookId, 0);
                } else if (response.status === 'exists' && response.summary) {
                    // Summary already exists, display it
                    displaySummary(response.summary, response.created_at);
                } else {
                    // Unexpected response
                    showError('Unexpected response from server');
                }
            },
            error: function(xhr) {
                var errorMsg = 'Failed to generate summary';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'AI features are disabled';
                } else if (xhr.status === 404) {
                    errorMsg = 'Book not found';
                } else if (xhr.status === 401) {
                    errorMsg = 'Unauthorized. Please log in.';
                }
                showError(errorMsg);
            }
        });
    }

    function showError(message) {
        $('#ai-summary-loading').hide();
        $('#ai-summary-error-message').text(message);
        $('#ai-summary-error').show();
        $('#generate-ai-summary').prop('disabled', false);
    }

    function displaySummary(summaryText, createdAt) {
        // Hide loading and error states
        $('#ai-summary-loading').hide();
        $('#ai-summary-error').hide();
        
        // Check if summary display panel exists
        var $summaryDisplay = $('#ai-summary-display');
        
        if ($summaryDisplay.length === 0) {
            // Create the summary panel if it doesn't exist
            var panelHtml = 
                '<div class="panel panel-default" id="ai-summary-display">' +
                    '<div class="panel-heading">' +
                        '<h4 class="panel-title">' +
                            '<span class="glyphicon glyphicon-info-sign"></span> AI Summary' +
                        '</h4>' +
                    '</div>' +
                    '<div class="panel-body" id="ai-summary-text"></div>' +
                    '<div class="panel-footer">' +
                        '<small id="ai-summary-date">Generated just now</small>' +
                    '</div>' +
                '</div>';
            
            // Insert after the error div
            $('#ai-summary-error').after(panelHtml);
            $summaryDisplay = $('#ai-summary-display');
            
            // Update the button to show "Regenerate" instead of "Generate"
            var $btn = $('#generate-ai-summary');
            $btn.data('has-summary', 'true');
            $btn.html('<span class="glyphicon glyphicon-refresh"></span> Regenerate Summary');
        }
        
        // Update summary content
        $('#ai-summary-text').html(summaryText);
        
        // Update date if provided
        if (createdAt) {
            $('#ai-summary-date').text('Generated on ' + createdAt);
        } else {
            $('#ai-summary-date').text('Generated just now');
        }
        
        // Show the panel with a nice fade effect
        $summaryDisplay.hide().fadeIn(300);
        
        // Re-enable buttons
        $('#generate-ai-summary').prop('disabled', false);
        
        // Update status badges (summary exists, embedding auto-generated)
        updateStatusBadges(true, true);
        
        // Show success message briefly
        showSuccessMessage('Summary generated successfully! Book is now searchable via AI Search.');
        
        // Get book ID from button data attribute
        var $btn = $('#generate-ai-summary');
        var bookId = $btn.data('book-id');
        
        // Refresh similar books after a short delay to ensure embedding is ready
        // Embedding is created synchronously, but give it a moment to be fully indexed
        if (bookId) {
            console.log('Summary generated, refreshing similar books for book ID:', bookId);
            setTimeout(function() {
                refreshSimilarBooks(bookId);
            }, 1000);
        } else {
            console.warn('Could not find book ID for refreshing similar books');
        }
    }

    function showSuccessMessage(message) {
        // Create temporary success alert
        var $alert = $(
            '<div class="alert alert-success alert-dismissible" role="alert" style="margin-top: 10px;">' +
                '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                    '<span aria-hidden="true">&times;</span>' +
                '</button>' +
                '<span class="glyphicon glyphicon-ok"></span> ' + message +
            '</div>'
        );
        
        // Insert after the button group
        $('.ai-summary-section .btn-group').after($alert);
        
        // Auto-dismiss after 3 seconds
        setTimeout(function() {
            $alert.fadeOut(300, function() {
                $(this).remove();
            });
        }, 3000);
    }

    function updateStatusBadges(hasSummary, hasEmbedding) {
        // Update summary badge
        var $summaryBadge = $('.ai-status-indicators .label:first');
        if (hasSummary) {
            $summaryBadge
                .removeClass('label-default')
                .addClass('label-success')
                .attr('title', 'AI summary has been generated for this book')
                .find('.glyphicon')
                .removeClass('glyphicon-minus')
                .addClass('glyphicon-ok');
        }
        
        // Update embedding badge (embeddings are auto-generated with summaries)
        var $embeddingBadge = $('#embedding-status-badge');
        if (hasEmbedding || hasSummary) {
            // If summary was just generated, embedding should be created too
            $embeddingBadge
                .removeClass('label-default')
                .addClass('label-success')
                .attr('title', 'Book is indexed for AI Search')
                .find('.glyphicon')
                .removeClass('glyphicon-minus')
                .addClass('glyphicon-ok');
        }
        
        // Reinitialize tooltips
        $('[data-toggle="tooltip"]').tooltip('destroy').tooltip();
    }

    function pollForSummary(bookId, attempt) {
        // Poll up to 30 times (5 minutes max at 10 second intervals)
        var maxAttempts = 30;
        var pollInterval = 5000; // 5 seconds (faster polling)
        
        if (attempt >= maxAttempts) {
            showError('Summary generation is taking longer than expected. Please refresh the page to check status.');
            return;
        }
        
        // Update loading message with progress
        var progressPercent = Math.min(95, Math.round((attempt / maxAttempts) * 100));
        $('#ai-summary-loading').html(
            '<div class="alert alert-info">' +
                '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' + 
                'Generating summary... (' + progressPercent + '%)' +
                '<div class="progress" style="margin-top: 10px; margin-bottom: 0;">' +
                    '<div class="progress-bar progress-bar-striped active" role="progressbar" ' +
                        'aria-valuenow="' + progressPercent + '" aria-valuemin="0" aria-valuemax="100" ' +
                        'style="width: ' + progressPercent + '%;">' +
                    '</div>' +
                '</div>' +
            '</div>'
        );
        
        // Check if summary exists
        $.ajax({
            url: '/api/ai/summary/' + bookId + '/status',
            method: 'GET',
            success: function(response) {
                if (response.status === 'exists' && response.summary) {
                    // Summary is ready, display it without page reload
                    displaySummary(response.summary, response.created_at);
                } else if (response.task_status === 'failed' && response.task_error) {
                    // Task failed, show error
                    showError('Summary generation failed: ' + response.task_error);
                } else if (response.task_status === 'running' || response.task_status === 'waiting') {
                    // Task still running, continue polling
                    setTimeout(function() {
                        pollForSummary(bookId, attempt + 1);
                    }, pollInterval);
                } else {
                    // Summary not ready yet, poll again
                    setTimeout(function() {
                        pollForSummary(bookId, attempt + 1);
                    }, pollInterval);
                }
            },
            error: function(xhr) {
                // On error, continue polling (might be temporary)
                if (attempt < 5) {
                    // Retry quickly for first few attempts
                    setTimeout(function() {
                        pollForSummary(bookId, attempt + 1);
                    }, 2000);
                } else {
                    // After 5 attempts, use normal interval
                    setTimeout(function() {
                        pollForSummary(bookId, attempt + 1);
                    }, pollInterval);
                }
            }
        });
    }

    function refreshSimilarBooks(bookId, attempt) {
        attempt = attempt || 0;
        var maxAttempts = 10; // Try up to 10 times
        var retryDelay = 2000; // Start with 2 seconds
        
        console.log('refreshSimilarBooks called for book ID:', bookId, 'attempt:', attempt);
        
        // Check if similar books section exists
        var $section = $('#similar-books-section');
        if ($section.length === 0) {
            console.warn('Similar books section not found on page');
            return; // Similar books section not on this page
        }
        
        // Show loading state (only on first attempt)
        var $content = $('#similar-books-content');
        if (attempt === 0) {
            $content.html(
                '<div class="alert alert-info">' +
                    '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' +
                    'Loading similar books...' +
                '</div>'
            );
        }
        
        // Fetch similar books from API
        $.ajax({
            url: '/api/ai/similar/' + bookId,
            method: 'GET',
            success: function(response) {
                console.log('Similar books API response:', response);
                
                // Check if embedding is not ready yet
                if (response.message && (response.message.indexOf('No embedding available') !== -1 || 
                    response.message.indexOf('Generate a summary first') !== -1)) {
                    console.log('Embedding not ready yet, retrying...');
                    // Embedding not ready yet, retry
                    if (attempt < maxAttempts) {
                        // Update loading message to show retry
                        $content.html(
                            '<div class="alert alert-info">' +
                                '<span class="glyphicon glyphicon-refresh glyphicon-spin"></span> ' +
                                'Waiting for embedding to be ready... (attempt ' + (attempt + 1) + '/' + maxAttempts + ')' +
                            '</div>'
                        );
                        setTimeout(function() {
                            refreshSimilarBooks(bookId, attempt + 1);
                        }, retryDelay);
                        return;
                    } else {
                        // Max attempts reached
                        $content.html(
                            '<div class="alert alert-warning">' +
                                '<span class="glyphicon glyphicon-warning-sign"></span> ' +
                                'Embedding is still being created. Please refresh the page in a moment.' +
                            '</div>'
                        );
                        return;
                    }
                }
                
                if (response.similar_books && response.similar_books.length > 0) {
                    console.log('Found', response.similar_books.length, 'similar books');
                    // Render similar books
                    renderSimilarBooks(response.similar_books);
                } else {
                    console.log('No similar books found');
                    // No similar books found (but embedding exists)
                    $content.html(
                        '<h3>' +
                            '<span class="glyphicon glyphicon-book"></span> ' +
                            'Similar Books' +
                        '</h3>' +
                        '<div class="alert alert-info">' +
                            '<span class="glyphicon glyphicon-info-sign"></span> ' +
                            (response.message || 'No similar books found yet. More books need AI summaries to find matches.') +
                        '</div>'
                    );
                }
            },
            error: function(xhr) {
                console.error('Error fetching similar books:', xhr.status, xhr.responseJSON || xhr.responseText);
                
                // Check if it's a "no embedding" error (404 or specific message)
                var errorMsg = 'Unable to load similar books';
                var shouldRetry = false;
                
                if (xhr.status === 404 || (xhr.responseJSON && xhr.responseJSON.message && 
                    xhr.responseJSON.message.indexOf('No embedding') !== -1)) {
                    // Embedding might not be ready yet, retry
                    console.log('No embedding error, retrying...');
                    shouldRetry = true;
                } else if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                
                if (shouldRetry && attempt < maxAttempts) {
                    // Retry with exponential backoff
                    setTimeout(function() {
                        refreshSimilarBooks(bookId, attempt + 1);
                    }, retryDelay);
                } else {
                    // Show error
                    $content.html(
                        '<div class="alert alert-warning">' +
                            '<span class="glyphicon glyphicon-warning-sign"></span> ' +
                            errorMsg +
                        '</div>'
                    );
                }
            }
        });
    }
    
    function renderSimilarBooks(similarBooks) {
        var $content = $('#similar-books-content');
        var html = '<h3>' +
            '<span class="glyphicon glyphicon-book"></span> ' +
            'Similar Books' +
        '</h3>' +
        '<div class="row display-flex">';
        
        // Limit to 8 books
        var booksToShow = similarBooks.slice(0, 8);
        
        booksToShow.forEach(function(item) {
            var book = item.book;
            var score = item.similarity_score || 0;
            
            // Build authors string - API returns authors as array of objects with id and name
            var authorsHtml = '';
            if (book.authors && book.authors.length > 0) {
                book.authors.forEach(function(author, index) {
                    if (index > 0) {
                        authorsHtml += '<span>&amp;</span> ';
                    }
                    // Escape HTML and truncate long author names
                    var safeName = $('<div>').text(author.name || '').html();
                    var displayName = safeName.length > 30 ? safeName.substring(0, 27) + '...' : safeName;
                    authorsHtml += '<a class="author-name" href="/author/' + (author.id || '') + '">' + displayName + '</a>';
                });
            }
            
            // Determine label class based on score
            var labelClass = 'default';
            if (score > 0.7) {
                labelClass = 'success';
            } else if (score > 0.4) {
                labelClass = 'info';
            }
            
            // Build similarity score badge
            var scoreBadge = '';
            if (score > 0) {
                scoreBadge = '<p class="similarity-score" style="margin-top: 5px;">' +
                    '<span class="label label-' + labelClass + '">' +
                        '<span class="glyphicon glyphicon-flash"></span> ' +
                        Math.round(score * 100) + '%' +
                    '</span>' +
                '</p>';
            }
            
            // Escape book title for HTML
            var safeTitle = $('<div>').text(book.title || 'Untitled').html();
            var shortTitle = safeTitle.length > 50 ? safeTitle.substring(0, 47) + '...' : safeTitle;
            
            // Build cover URL with cache-busting parameter
            var coverUrl = '/cover/' + book.id + '/og';
            if (book.last_modified) {
                coverUrl += '?c=' + book.last_modified;
            } else {
                // Fallback to current timestamp if last_modified not available
                coverUrl += '?c=' + Date.now();
            }
            
            html += '<div class="col-sm-3 col-lg-2 col-xs-6 book">' +
                '<div class="cover">' +
                    '<a href="/book/' + book.id + '">' +
                        '<span class="img" title="' + $('<div>').text(safeTitle).html() + '">' +
                            '<img src="' + coverUrl + '" alt="' + $('<div>').text(safeTitle).html() + '" ' +
                            'onerror="this.onerror=null; this.src=\'/static/generic_cover.jpg\';" />' +
                        '</span>' +
                    '</a>' +
                '</div>' +
                '<div class="meta">' +
                    '<a href="/book/' + book.id + '">' +
                        '<p title="' + $('<div>').text(safeTitle).html() + '" class="title">' +
                            shortTitle +
                        '</p>' +
                    '</a>' +
                    '<p class="author">' + authorsHtml + '</p>' +
                    scoreBadge +
                '</div>' +
            '</div>';
        });
        
        html += '</div>';
        $content.html(html);
        
        // Fade in the updated content
        $content.hide().fadeIn(300);
    }

    // Initialize on document ready
    $(document).ready(function() {
        // Single button handles both generate and regenerate
        $('#generate-ai-summary').on('click', function() {
            var $btn = $(this);
            var bookId = $btn.data('book-id');
            var hasSummary = $btn.data('has-summary') === true || $btn.data('has-summary') === 'true';
            
            // If summary exists, regenerate; otherwise generate new
            generateSummary(bookId, hasSummary);
        });
    });
})();
