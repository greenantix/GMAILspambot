Phase 1: Implementing Server-Side Filtering
Objective: Refactor the core processing logic to leverage server-side filtering via the Gmail API, eliminating the primary performance bottleneck and addressing the "incomplete inbox processing" failure.

Task 1.1: Enhance the Filter Harvester for Server-Side Actions
Reasoning: The current filter_harvester.py can read filters but its output isn't ready for direct use in server-side batch operations. We need to ensure it can translate human-readable label names back into the labelIds the API requires for modification actions.

Target File: tools/filter_harvester.py

Implementation Steps:

Create a Name-to-ID Cache: Just as there is a _label_id_to_name_cache, create a reverse cache _label_name_to_id_cache to avoid redundant API calls when finding a label's ID.

Implement _get_label_id_from_name: Create this new helper function. It will first check the cache. If the name is not found, it will call service.users().labels().list() once, populate the entire cache with all user labels, and then return the requested ID. This is far more efficient than making a separate API call for every single label name.

Complete _apply_filter_action: This is the most critical fix.

The function is currently a no-op because it doesn't translate label names in the action_data back to labelIds.

Use the new _get_label_id_from_name helper to convert all label names in action_data['add_labels'] into a list of labelIds.

Construct the modifications dictionary with the correct addLabelIds and removeLabelIds.

Use wrap_gmail_api_call to execute the service.users().messages().modify() call.

Refine apply_existing_filters_to_backlog: This function's purpose will now shift to a more direct, server-side application.

It should iterate through each harvested filter.

For each filter, it will call service.users().messages().list(q=filter['query']) to get all matching message IDs, handling pagination with nextPageToken until no more pages are returned.

Once it has the complete list of IDs for a given filter, it will use service.users().messages().batchModify() to apply the filter's action to all of them in a single call.

It will return detailed stats on which filters were applied and how many messages each one affected.

Task 1.2: Refactor bulk_processor.py to Use the New Strategy
Reasoning: The bulk_processor.py script is the primary tool for handling large backlogs. We must replace its inefficient client-side loop with the new server-side filtering strategy.

Target File: bulk_processor.py

Implementation Steps:

Remove Old Logic: Gut the process_with_strategy function. The old logic of analyzing a small batch and then trying to exclude senders is now obsolete.

Implement New Workflow:

Phase 1 - Server-Side Filtering: The first step is now to call a new function, let's name it run_server_side_filter_pass().

This function will call fetch_and_parse_filters() from the enhanced filter_harvester.

It will then loop through each filter and use the new, robust apply_existing_filters_to_backlog to process emails matching that filter.

Log the results of each filter application (e.g., "Filter 'Newsletters' processed 1,253 emails.").

Phase 2 - LLM Processing for Remainder: After the server-side pass is complete, the remaining emails (those untouched by any filter) need to be processed by the LLM.

Construct a query for the process_email_backlog function that retrieves only unread emails in the inbox that do not have any of the labels that were applied during Phase 1. The query will look something like: is:unread in:inbox -has:userlabels or more specifically is:unread in:inbox -label:BILLS -label:SHOPPING ....

Call cleaner.process_email_backlog with this highly targeted query.

Update Logging and UI Callbacks: Ensure the log_callback and progress_callback functions are updated to reflect this new two-phase process, providing clear feedback to the user about what's happening.

This phase fundamentally changes the engine of the application from a sputtering client-side script to an efficient server-side processor, directly addressing the user's primary complaint about incomplete processing.
