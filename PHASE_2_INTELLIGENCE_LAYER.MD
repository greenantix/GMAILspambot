PHASE_2_INTELLIGENCE_LAYER.md
Task 2.1: Implement the Email Learning Engine
Problem: The EmailLearningEngine is a powerful concept in the project but its core methods (suggest_rule_updates, detect_new_patterns) are placeholders.
Files to Modify: gmail_lm_cleaner.py (within EmailLearningEngine class)
Implementation Steps:
suggest_rule_updates:
Load the categorization_history.json log.
Iterate through the history, looking for entries where user_override is present and differs from llm_action.
Use a dictionary to count correction patterns (e.g., {'sender@example.com': {'from_JUNK_to_BILLS': 5}}).
If a pattern's count exceeds a threshold (e.g., 3), generate a concrete suggestion:
Suggestion Type: sender_correction
Details: {'sender': 'sender@example.com', 'suggested_category': 'BILLS', 'reason': 'User consistently moved this sender from JUNK to BILLS.'}
detect_new_patterns:
Filter the history for emails that were categorized as REVIEW (low confidence).
Use simple clustering: group these REVIEW emails by sender domain.
If a domain cluster has more than a threshold number of emails (e.g., 10), analyze the subjects for common keywords (e.g., by splitting subjects into words and finding the most frequent ones).
Generate a new_pattern suggestion: {'type': 'domain', 'identifier': 'some-new-service.com', 'common_keywords': ['invoice', 'receipt'], 'email_count': 12, 'suggested_category': 'BILLS'}.
apply_learning_suggestions (in GmailCleanerGUI):
This function is called when the user clicks "Apply Suggestions" on the Analytics tab.
It should take the generated suggestions and programmatically edit the rule files in the rules/ directory.
For a sender_correction, open the corresponding JSON file (e.g., rules/BILLS.json), load the data, append the new sender to the senders list, and save the file.
Provide feedback to the user via the log and a messagebox.
Task 2.2: Activate the Analytics Dashboard
Problem: The Analytics tab in the GUI is currently filled with placeholder data.
File to Modify: gmail_lm_cleaner.py (within GmailCleanerGUI class, specifically refresh_analytics and its helpers)
Implementation Steps:
Modify generate_analytics_data to be the single source of truth. It should run the suggest_rule_updates and detect_new_patterns from the learning engine. It should also calculate statistics from categorization_history.json.
In update_analytics_ui, pass the generated data to the helper functions.
draw_category_pie_chart: This function is well-implemented. Ensure it receives real data from generate_analytics_data.
update_filter_effectiveness: Replace the placeholder data. Calculate "User Satisfaction" as 100 - override_rate. Calculate "LLM Classification" as the average confidence score from the history.
update_learning_insights & update_suggestions_display: These text boxes should be populated with the formatted output from the (now functional) learning engine suggestions.
