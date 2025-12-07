/**
 * Book Chatbot JavaScript
 * Handles chatbot UI interactions for asking questions about books
 */

(function() {
    'use strict';

    var conversationHistory = [];
    var availabilityCheckInProgress = false;

    /**
     * Load conversation history from localStorage
     */
    function loadChatHistory(bookId) {
        try {
            var storageKey = 'chatbot_history_' + bookId;
            var stored = localStorage.getItem(storageKey);
            if (stored) {
                var parsed = JSON.parse(stored);
                
                // Validate structure
                if (Array.isArray(parsed)) {
                    conversationHistory = parsed.filter(function(exchange) {
                        return exchange && 
                               typeof exchange === 'object' &&
                               typeof exchange.question === 'string' &&
                               typeof exchange.answer === 'string';
                    });
                } else {
                    conversationHistory = [];
                }
                
                // Restore messages to UI
                $('#chatbot-history').empty();
                conversationHistory.forEach(function(exchange) {
                    // Convert ISO timestamp to locale string for display
                    var displayTimestamp = exchange.timestamp ? 
                        new Date(exchange.timestamp).toLocaleTimeString() : 
                        new Date().toLocaleTimeString();
                    displayMessage('user', exchange.question, displayTimestamp);
                    displayMessage('bot', exchange.answer, displayTimestamp);
                });
            }
        } catch (e) {
            console.error('Error loading chat history:', e);
            conversationHistory = [];
        }
    }

    /**
     * Save conversation history to localStorage
     */
    function saveChatHistory(bookId) {
        try {
            var storageKey = 'chatbot_history_' + bookId;
            localStorage.setItem(storageKey, JSON.stringify(conversationHistory));
        } catch (e) {
            if (e.name === 'QuotaExceededError') {
                console.warn('localStorage quota exceeded, clearing old history');
                // Clear oldest entries and retry
                conversationHistory = conversationHistory.slice(-5);
                try {
                    localStorage.setItem(storageKey, JSON.stringify(conversationHistory));
                } catch (e2) {
                    console.error('Error saving chat history after quota cleanup:', e2);
                }
            } else {
                console.error('Error saving chat history:', e);
            }
        }
    }

    /**
     * Check if chatbot is available for a book
     */
    function checkChatbotAvailability(bookId) {
        if (availabilityCheckInProgress) {
            return; // Already checking, prevent race condition
        }
        availabilityCheckInProgress = true;
        
        $.ajax({
            url: '/api/ai/chatbot/' + bookId + '/status',
            method: 'GET',
            success: function(response) {
                if (response.available) {
                    $('#chatbot-section').show();
                    $('#chatbot-not-indexed').hide();
                } else {
                    $('#chatbot-section').hide();
                    if (!response.book_indexed) {
                        $('#chatbot-not-indexed').show();
                    }
                }
            },
            error: function() {
                $('#chatbot-section').hide();
            },
            complete: function() {
                availabilityCheckInProgress = false;
            }
        });
    }

    /**
     * Send a question to the chatbot
     */
    function sendQuestion(bookId, question) {
        if (!question || !question.trim()) {
            return;
        }

        var questionText = question.trim();
        
        // Validate question length
        if (questionText.length > 1000) {
            displayMessage('error', 'Question is too long (maximum 1000 characters)');
            return;
        }
        
        // Disable input and show loading
        $('#chatbot-input').prop('disabled', true);
        $('#chatbot-send-btn').prop('disabled', true);
        
        // Display user question
        displayMessage('user', questionText);
        
        // Show "Thinking..." message
        var thinkingId = 'thinking-' + Date.now();
        displayMessage('bot', 'Thinking...', null, thinkingId);
        
        // Scroll to bottom
        scrollChatToBottom();
        
            // Prepare conversation history for API (last 5 exchanges only, without timestamps)
            var apiHistory = [];
            try {
                apiHistory = conversationHistory.slice(-5).map(function(exchange) {
                    // Ensure we only send question and answer (strip any extra fields like timestamp)
                    var cleanExchange = {
                        question: String(exchange.question || ''),
                        answer: String(exchange.answer || '')
                    };
                    // Validate that both fields exist and are non-empty
                    if (!cleanExchange.question || !cleanExchange.answer) {
                        console.warn('Skipping invalid exchange:', exchange);
                        return null;
                    }
                    return cleanExchange;
                }).filter(function(ex) { return ex !== null; }); // Remove null entries
            } catch (e) {
                console.error('Error preparing conversation history:', e);
                apiHistory = []; // Fallback to empty array
            }
            
            // Prepare request payload
            var requestPayload = {
                question: questionText,
                conversation_history: apiHistory
            };
            
            console.log('Sending chatbot request:', {
                bookId: bookId,
                questionLength: questionText.length,
                historyLength: apiHistory.length,
                payload: requestPayload
            });
            
            // Make API call
        $.ajax({
            url: '/api/ai/chatbot/' + bookId + '/ask',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requestPayload),
            success: function(response) {
                // Remove thinking message
                $('#' + thinkingId).remove();
                
                if (response.error) {
                    displayMessage('error', response.error);
                } else {
                    displayMessage('bot', response.answer);
                    
                    // Add to conversation history with timestamp
                    var timestamp = new Date().toISOString();
                    conversationHistory.push({
                        question: questionText,
                        answer: response.answer,
                        timestamp: timestamp
                    });
                    
                    // Keep history limited (last 10 exchanges for localStorage, but only send last 5 to API)
                    if (conversationHistory.length > 10) {
                        conversationHistory.shift();
                    }
                    
                    // Save to localStorage
                    saveChatHistory(bookId);
                }
                
                // Re-enable input
                $('#chatbot-input').prop('disabled', false);
                $('#chatbot-send-btn').prop('disabled', false);
                $('#chatbot-input').focus();
                
                scrollChatToBottom();
            },
            error: function(xhr) {
                // Remove thinking message
                $('#' + thinkingId).remove();
                
                // Log detailed error for debugging
                console.error('Chatbot API Error:', JSON.stringify({
                    status: xhr.status,
                    statusText: xhr.statusText,
                    response: xhr.responseJSON || xhr.responseText,
                    responseText: xhr.responseText,
                    url: xhr.responseURL || '/api/ai/chatbot/' + bookId + '/ask',
                    requestData: {
                        question: questionText,
                        historyLength: apiHistory.length
                    }
                }, null, 2));
                
                var errorMsg = 'Failed to get answer';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMsg = 'Chatbot feature is disabled';
                } else if (xhr.status === 404) {
                    errorMsg = 'Book not found';
                } else if (xhr.status === 400) {
                    errorMsg = xhr.responseJSON && xhr.responseJSON.error 
                        ? xhr.responseJSON.error 
                        : 'Invalid request: ' + (xhr.responseText || xhr.statusText);
                } else if (xhr.status === 500) {
                    errorMsg = 'Server error. Please try again.';
                } else if (xhr.status === 503) {
                    errorMsg = 'Service unavailable. Please check AI configuration.';
                }
                
                displayMessage('error', errorMsg);
                
                // Re-enable input
                $('#chatbot-input').prop('disabled', false);
                $('#chatbot-send-btn').prop('disabled', false);
                $('#chatbot-input').focus();
                
                scrollChatToBottom();
            }
        });
    }

    /**
     * Escape HTML entities to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    /**
     * Display a message in the chat history
     */
    function displayMessage(role, text, timestamp, messageId) {
        if (!timestamp) {
            timestamp = new Date().toLocaleTimeString();
        }
        
        var messageIdAttr = messageId ? 'id="' + escapeHtml(messageId) + '"' : '';
        var cssClass = 'list-group-item';
        var icon = '';
        
        if (role === 'user') {
            cssClass += ' list-group-item-info text-right';
            icon = '<span class="glyphicon glyphicon-user"></span> ';
        } else if (role === 'error') {
            cssClass += ' list-group-item-danger';
            icon = '<span class="glyphicon glyphicon-exclamation-sign"></span> ';
        } else {
            cssClass += ' list-group-item-default';
            icon = '<span class="glyphicon glyphicon-comment"></span> ';
        }
        
        // Escape HTML to prevent XSS
        var escapedText = escapeHtml(text).replace(/\n/g, '<br>');
        var escapedTimestamp = escapeHtml(timestamp);
        
        var messageHtml = 
            '<li class="' + cssClass + '" ' + messageIdAttr + '>' +
                '<div>' + icon + escapedText + '</div>' +
                '<small class="text-muted">' + escapedTimestamp + '</small>' +
            '</li>';
        
        $('#chatbot-history').append(messageHtml);
        scrollChatToBottom();
    }

    /**
     * Clear chat history
     */
    function clearChat(bookId) {
        $('#chatbot-history').empty();
        conversationHistory = [];
        
        // Clear from localStorage
        if (bookId) {
            try {
                var storageKey = 'chatbot_history_' + bookId;
                localStorage.removeItem(storageKey);
            } catch (e) {
                console.error('Error clearing chat history:', e);
            }
        }
        
    }

    /**
     * Scroll chat history to bottom
     */
    function scrollChatToBottom() {
        var $chatHistory = $('#chatbot-history');
        $chatHistory.scrollTop($chatHistory[0].scrollHeight);
    }

    /**
     * Handle Enter key press
     */
    function handleEnterKey(event) {
        if (event.keyCode === 13 && !event.shiftKey) {
            event.preventDefault();
            var bookId = $('#chatbot-input').data('book-id');
            var question = $('#chatbot-input').val();
            if (question && question.trim()) {
                sendQuestion(bookId, question);
                $('#chatbot-input').val('');
            }
        }
    }

    // Initialize when DOM is ready
    $(document).ready(function() {
        var $chatbotInput = $('#chatbot-input');
        var $chatbotSendBtn = $('#chatbot-send-btn');
        var $chatbotClearBtn = $('#chatbot-clear-btn');
        
        if ($chatbotInput.length > 0) {
            var bookId = $chatbotInput.data('book-id');
            
            // Check availability on load
            checkChatbotAvailability(bookId);
            
            // Load chat history from localStorage
            loadChatHistory(bookId);
            
            // Set up event handlers
            $chatbotSendBtn.on('click', function() {
                var question = $chatbotInput.val();
                if (question && question.trim()) {
                    sendQuestion(bookId, question);
                    $chatbotInput.val('');
                }
            });
            
            $chatbotInput.on('keypress', handleEnterKey);
            
            if ($chatbotClearBtn.length > 0) {
                $chatbotClearBtn.on('click', function() {
                    clearChat(bookId);
                });
            }
            
        }
    });

    // Expose functions for external use if needed
    window.BookChatbot = {
        sendQuestion: sendQuestion,
        clearChat: clearChat,
        checkAvailability: checkChatbotAvailability
    };

})();

