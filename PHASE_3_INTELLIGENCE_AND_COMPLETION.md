Phase 3: Intelligence and Feature Completion
Objective: With a stable and reliable foundation, the final step is to implement the advanced "intelligent" features that are currently placeholders and complete the user-facing workflows.

Task 3.1: Implement the Email Learning Engine's Core Logic
Reasoning: The EmailLearningEngine is the heart of the bot's long-term intelligence. Its ability to learn from user corrections is what will make the system truly personalized and powerful. This functionality is currently incomplete.

Files to Modify: gmail_lm_cleaner.py (specifically EmailLearningEngine and the apply_rule_suggestions method in GmailCleanerGUI)

Implementation Steps:

Implement suggest_rule_updates in EmailLearningEngine:

This function should load and parse the logs/categorization_history.json file.

It must identify every instance where user_override exists and is different from llm_action.

It should aggregate these corrections. For example, if the user moves emails from "sender@example.com" to the "BILLS" category five times, the engine should generate a high-confidence suggestion to add this sender to the rules/BILLS.json file.

The function should return a structured dictionary of suggestions, including the proposed change, the evidence (e.g., "Corrected 5 times"), and a confidence score.

Implement detect_new_patterns in EmailLearningEngine:

This function should filter the history for all emails that were categorized as REVIEW.

It should then perform clustering on these emails. A simple but effective method is to group them by sender's domain name (e.g., group_by('domain.com')).

If a cluster is large enough (e.g., >10 emails from newservice.com), analyze the subjects within that cluster for common keywords (e.g., using TF-IDF or simple word frequency).

Generate a suggestion to create a new rule for this domain, possibly with the identified keywords.

Implement apply_rule_suggestions in GmailCleanerGUI:

This function gets called when the user clicks the "Apply Suggestions" button in the Analytics tab.

It must take the list of structured suggestions from the learning engine.

For each suggestion, it will programmatically open the relevant JSON file in the rules/ directory, load the JSON data, append the new sender or keyword to the appropriate list, and save the file back to disk.

This completes the feedback loop: the system makes a mistake, the user corrects it, the engine learns from the correction, and the system applies that learning to its own rules.

Task 3.2: Complete the Unsubscribe Workflow
Reasoning: The unsubscribe feature currently identifies candidates but doesn't take the final, crucial step of unsubscribing. This leaves the user with manual work.

Files to Modify: gmail_lm_cleaner.py

Implementation Steps:

Enhance OAuth Scopes: Add the https://www.googleapis.com/auth/gmail.send scope to the SCOPES list. This is necessary to send mailto: unsubscribe requests. The relogin_gmail function in the GUI should be used to get user consent for this new scope.

Implement mailto: Unsubscribing: In the attempt_unsubscribe function:

Check if the unsubscribe_info dictionary contains an email address.

If it does, use the googleapiclient to create a simple, raw MIME message (MIMEMultipart).

The message should be addressed to the unsubscribe email address, and the subject/body can often be left blank or contain the word "unsubscribe".

Use service.users().messages().send() to send the message from the user's account.

UI Feedback and Confirmation:

Before sending any emails, the unsubscribe_selected function must show a messagebox.askyesno dialog that clearly states: "This will send unsubscribe emails from your Gmail account. Do you want to proceed?"

After the process is complete, provide a summary dialog: "Successfully sent 5 unsubscribe requests. Failed on 1 (no unsubscribe link found)."

Task 3.3: Finalize the Rule Editor and Management Tab
Reasoning: The rule management tab allows viewing and editing, but the workflow for creating and managing new rules can be improved.

File to Modify: gmail_lm_cleaner.py (GmailCleanerGUI class)

Implementation Steps:

Streamline New Rule Creation: When a user clicks "Create New Rule", instead of just opening a blank template, guide them. Open a small dialog that asks for:

The name of the new label/rule.

The primary action (Archive, Trash, Keep in Inbox).

This information will be used to pre-populate the actions section of the JSON template, making it easier for the user.

Validate on Save: The validate_rule_format button is good, but validation should also happen automatically when the user clicks "Save Rule". If the JSON is invalid, the save should be prevented, and an error message should be shown.

Delete Rules and Labels Together: When a user deletes a label from the "Gmail Label Manager," the application should check if a corresponding rule file exists in the rules/ directory (e.g., rules/MyOldLabel.json). If it does, it should ask the user: "A rule file exists for this label. Do you want to delete it as well?" This keeps the rules and labels in sync.
