PHASE_3_FEATURE_COMPLETION_AND_USABILITY.md
Task 3.1: Finalize the Unsubscribe Workflow
Problem: The unsubscribe feature finds candidates but doesn't fully automate the action. The UI for this is also basic.
File to Modify: gmail_lm_cleaner.py
Implementation Steps:
UI Enhancement: In display_unsubscribe_candidates, instead of just showing text, create a frame for each candidate containing a ttk.Checkbutton and a label with the sender/subject information. This allows users to select specific senders.
Action Implementation (attempt_unsubscribe):
For unsubscribe links that are URLs, the current implementation using webbrowser.open() is a reasonable and safe first step.
For mailto: links, implement the logic to send the unsubscribe email. This will require adding the https://www.googleapis.com/auth/gmail.send scope to SCOPES and creating a simple MIME message to send to the specified address. Warning: Inform the user clearly that this will send an email from their account.
Task 3.2: Improve the Rule Editor UI/UX
Problem: The "ugly" UI is a user concern. The Rule & Label Management tab, while functional, can be improved.
File to Modify: gmail_lm_cleaner.py
Implementation Steps:
Enable Saving: The save_rule_btn is already in the UI. Ensure the save_rule_details function is robust. It should validate the JSON content before saving and provide clear error messages.
Auto-load on Connect: When the connect_gmail function succeeds, it should automatically trigger refresh_labels and refresh_rule_labels to populate the management tab.
Better Visuals: Instead of a plain text box for label action mappings, consider a more structured ttk.Treeview widget to display the labels and their associated actions in a clean, table-like format.
Simplify Rule Creation: The create_new_rule function currently uses a generic template. It could be improved by prompting the user for the intended action (LABEL_AND_ARCHIVE, TRASH, etc.) and pre-filling the actions part of the JSON template accordingly.
