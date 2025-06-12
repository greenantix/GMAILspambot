Project GreenAntix: High-Level Remediation Plan
Objective: To transition the greenantix-gmailspambot from its current unstable state to a reliable, efficient, and fully functional application.

This plan addresses the three core user-reported failures:

Incomplete Mail Processing: The bot fails to process the entire inbox, stopping after a small batch.

Silent Feature Failures: The "Auto Gemini" analysis and other features fail without providing feedback to the user.

General Instability: The application is prone to crashing due to unhandled errors and incomplete logic.

The New Core Strategy: Server-Side First
The most significant architectural change is moving from a client-side analysis model to a server-side first model for bulk processing. Instead of fetching 50,000 emails and analyzing them locally, the bot will now leverage the power of the Gmail API to perform filtering and labeling directly on Google's servers.

The Workflow Transformation:

Old (Inefficient) Method

New (Server-Side) Method

1. Fetch a page of 100 emails from the inbox.

1. Harvest all user filters from Gmail settings.

2. For each email, check if it matches any user-defined filters or rules.

2. For each filter, construct a Gmail API search query.

3. If it matches, apply a label (one API call per email).

3. Execute the search query to get a list of all matching message IDs (one API call).

4. If no rules match, send to LLM for analysis.

4. Use a single batchModify call to apply the filter's action to all found messages.

5. Repeat for the next page, often failing silently on errors.

5. Only emails that remain unaffected by any filter are then processed by the LLM.

This new approach is vastly more efficient, reducing thousands of API calls to a handful and providing a clear path to processing the entire backlog.

Phased Implementation Plan
This project will be completed in the following phases. Each phase is detailed in a corresponding .md file.

PHASE_1_SERVER_SIDE_FILTERING.md: Implement the new core strategy. This is the most critical phase and addresses the "incomplete processing" issue directly.

PHASE_2_STABILITY_AND_UI_REFINEMENT.md: Focus on eliminating crashes and providing robust feedback to the user. This fixes the silent failure of the Gemini and other features.

PHASE_3_INTELLIGENCE_AND_COMPLETION.md: With a stable foundation, implement the advanced learning and analytics features that are currently placeholders.

You are to begin with PHASE_1_SERVER_SIDE_FILTERING.md and proceed through the roadmap without stopping.
