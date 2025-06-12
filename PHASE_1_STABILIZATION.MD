PHASE_1_STABILIZATION.md
Task 1.1: Fix the Premature Backlog Termination Bug (CRITICAL)
Problem: The process_email_backlog function in gmail_lm_cleaner.py has a fatal flaw. A try...except Exception block wraps the API call to fetch a page of messages and contains a break statement. A single transient network error causes the entire bulk processing to stop silently, making it appear "done" when it has only processed a fraction of the emails.

File to Modify: gmail_lm_cleaner.py

Implementation Steps:

Locate the while True: loop inside the process_email_backlog function.
Find the try...except block that wraps the self.service.users().messages().list(...).execute() call.
Replace the break statement in the except block with continue. This ensures that if one page fetch fails, the loop will attempt to fetch the next page instead of terminating.
Add a counter to prevent an infinite loop on persistent errors. If the API call fails, say, 5 consecutive times, then it's safe to break the loop and log a critical error.
Python

# In gmail_lm_cleaner.py -> process_email_backlog()

# ... inside the while True loop ...
consecutive_errors = 0
while True:
    try:
        results = self.service.users().messages().list(
            # ... params ...
        ).execute()
        consecutive_errors = 0 # Reset on success
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Error fetching email batch: {e}")
        stats['errors'] += 1
        consecutive_errors += 1
        if consecutive_errors >= 5:
            log_callback("❌ Aborting backlog processing after 5 consecutive fetch errors.")
            self.logger.error("Aborting backlog processing due to repeated API fetch errors.")
            break # Break after too many failures
        time.sleep(5) # Wait before retrying the next page
        continue # Instead of break, continue to the next iteration

    # ... rest of the loop ...
Task 1.2: Implement Robust UI Error Feedback
Problem: When a background thread in the GUI fails, the error is logged to the console, but the user receives no feedback. The UI can appear frozen or unresponsive.

File to Modify: gmail_lm_cleaner.py (within the GmailCleanerGUI class)

Implementation Steps:

Create a dedicated method, e.g., _show_error_dialog(title, message). This method should use self.root.after(0, ...) to ensure the messagebox is called from the main UI thread.
In every background thread function (e.g., _auto_analyze_thread, _backlog_cleanup_thread, _export_subjects_thread), wrap the entire contents in a try...except...finally block.
In the except block, call self._show_error_dialog with details from the exception.
In the finally block, ensure any disabled buttons are re-enabled and status text is reset. This guarantees the UI becomes responsive again, regardless of success or failure.
Python

# In gmail_lm_cleaner.py -> GmailCleanerGUI class

def _show_error_dialog(self, title, message):
    """Thread-safe method to show an error message box."""
    self.root.after(0, lambda: messagebox.showerror(title, message))

def _auto_analyze_thread(self):
    """Thread function for auto-analyzing with Gemini."""
    try:
        self.find_candidates_btn.config(state='disabled', text="Analyzing...")
        # ... existing logic ...
    except Exception as e:
        error_message = f"Auto-analysis failed: {e}\n\nCheck logs for details."
        self.log(f"❌ {error_message}")
        self._show_error_dialog("Auto-Analysis Error", error_message)
    finally:
        # This block ALWAYS runs, ensuring the UI is unlocked
        self.root.after(0, lambda: self.find_candidates_btn.config(state='normal', text="Auto-Analyze with Gemini"))

Task 1.3: Make Filter Harvesting Functional
Problem: tools/filter_harvester.py has placeholder logic (pass) and is not correctly applying actions. This cripples the "filter-first" strategy of the bulk processor.
File to Modify: tools/filter_harvester.py
Implementation Steps:
The function _apply_filter_action needs to be completed.
It already correctly identifies the addLabelIds and removeLabelIds from the filter rule.
The missing piece is the call to the Gmail API. Use the gmail_api_utils.wrap_gmail_api_call to perform a service.users().messages().modify() operation with the constructed modifications body. This ensures the labels are actually applied to the email.
Ensure that apply_existing_filters_to_backlog returns not just the count of processed emails but also a list of the message IDs that were not processed by filters, so they can be passed to the next stage (LLM analysis). The current implementation in gmail_lm_cleaner.py already expects this (remaining_ids).
