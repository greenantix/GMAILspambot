Phase 2: Stability and UI Refinement
Objective: Address the silent failures and application crashes by implementing comprehensive error handling, robust process management, and clear user feedback mechanisms.

Task 2.1: Implement Global and Thread-Specific Exception Handling
Reasoning: The application currently suffers from silent failures, especially in the GUI, where background threads crash without informing the user. We must catch and report every critical error.

File to Modify: gmail_lm_cleaner.py (specifically the GmailCleanerGUI class), autonomous_runner.py

Implementation Steps:

Global UI Exception Handler (GmailCleanerGUI):

Implement the handle_ui_exception function. This function will be the last line of defense for the GUI.

In the __init__ method of the GmailCleanerGUI class, set self.root.report_callback_exception = self.handle_ui_exception. This tells Tkinter to call your function whenever an error occurs in an event callback.

The handler function should log the full traceback and then display a user-friendly messagebox.showerror, explaining that an error occurred and that the UI state is being reset.

Per-Thread try...finally Blocks (GmailCleanerGUI):

Go through every function that starts a thread (e.g., _auto_analyze_thread, _backlog_cleanup_thread, unsubscribe_selected).

Wrap the entire body of the thread's target function in a try...finally block.

The finally block must contain the code to re-enable any disabled buttons and reset status labels (e.g., self.unsubscribe_selected_btn.config(state='normal', text="Unsubscribe Selected")). This guarantees the UI never gets stuck in a disabled state.

Refined Exception Handling in autonomous_runner.py:

Replace the generic except Exception in the main while loop.

Create specific except blocks for AuthenticationError, LLMConnectionError, and GmailAPIError.

If an AuthenticationError occurs, log a CRITICAL message and break the loop, as this is unrecoverable.

If a recoverable error like LLMConnectionError occurs, log a WARNING and continue after a short delay.

Task 2.2: Refine the Auto-Gemini Workflow
Reasoning: The "Auto-Analyze with Gemini" feature fails silently. This is a direct result of the lack of robust error handling in the UI's background threads.

File to Modify: gmail_lm_cleaner.py (_auto_analyze_thread and show_confirmation_dialog in GmailCleanerGUI)

Implementation Steps:

Apply the try...finally pattern from Task 2.1 to the _auto_analyze_thread function.

In the except block of the thread, call the _show_error_dialog method to inform the user exactly why the analysis failed (e.g., "Gemini API key is invalid," "Network connection failed," "Could not parse Gemini's response").

Modify the show_confirmation_dialog function. It currently shows a generic error if proposed_rules is empty. It should now expect a more structured result from the analysis function, perhaps a tuple (success, result_or_error_message). This allows it to display a specific, helpful error message in the confirmation dialog window itself, rather than just in a separate popup.

Task 2.3: Revise the UI for Clarity and Professionalism
Reasoning: The user mentioned the UI is "ugly." While a full rewrite to a different framework is out of scope, we can significantly improve the existing Tkinter UI's clarity and professionalism.

File to Modify: gmail_lm_cleaner.py (GmailCleanerGUI class)

Implementation Steps:

Consistent Styling: Use the ttk.Style object to define a consistent theme for all widgets. Define styles for TButton, TLabel, TFrame, TProgressbar, etc. Use a clean, modern theme like 'clam' or 'alt'.

Improve Layout and Spacing: Add padding (padx, pady) to all pack() or grid() calls to give elements breathing room. Use ttk.Separator widgets to visually divide distinct sections within tabs.

Redesign the Rule Editor: The scrolledtext widget for editing JSON rules is functional but not user-friendly.

Add line numbers to the text widget.

Add basic syntax highlighting for JSON (different colors for keys, strings, numbers, booleans). This can be achieved by using text widget tags and regularly parsing the content to re-apply the tags.

Actionable Analytics:

In the "Analytics" tab, make the suggestions actionable. Next to each suggestion in the optimizations_text widget, add a small "Apply" button that triggers the specific action (e.g., adding a sender to a rule file). This is more intuitive than the single "Apply All" button.

By completing this phase, the application will be significantly more stable, provide better feedback, and feel more polished and professional to the user.
