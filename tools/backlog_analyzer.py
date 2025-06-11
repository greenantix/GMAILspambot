"""
backlog_analyzer.py

This module provides tools for analyzing large email backlogs (75k+ emails)
to identify patterns and inform processing strategies. It is designed to be
memory-efficient, using generators and batch processing to handle large datasets
without loading everything into memory at once.

Key Features:
-   analyze_backlog: Main entry point to perform a full analysis.
-   _fetch_emails_in_batches: Generator to fetch emails page by page.
-   _process_batch_for_analysis: Processes a single batch of emails to extract key metadata.
-   generate_sender_frequency: Creates a report of the most common senders.
-   identify_volume_patterns: Analyzes email volume over date ranges.
-   suggest_batch_strategies: Recommends optimal batch sizes and queries.
-   export_analysis_report: Exports the findings to JSON or CSV.

Dependencies:
-   google-api-python-client
-   pandas (for data manipulation and export)

Usage:
    from tools.backlog_analyzer import analyze_backlog
    from gmail_api_utils import get_gmail_service

    service = get_gmail_service()
    if service:
        analysis_report = analyze_backlog(service, query="is:unread", max_emails=10000)
        export_analysis_report(analysis_report, "backlog_analysis.json")
"""

import logging
from typing import List, Dict, Any, Generator, Tuple
from collections import Counter
import pandas as pd
import json
from datetime import datetime

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

# Initialize logger
logger = logging.getLogger(__name__)


def _fetch_emails_in_batches(
    service: Resource, query: str, max_emails: int, batch_size: int = 100
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    A generator that fetches emails in batches to conserve memory.

    Args:
        service (Resource): Authenticated Gmail API service.
        query (str): The Gmail search query.
        max_emails (int): The total maximum number of emails to fetch.
        batch_size (int): The number of email IDs to fetch per API call.

    Yields:
        Generator[List[Dict[str, Any]], None, None]: A list of email message objects.
    """
    try:
        page_token = None
        emails_fetched = 0
        while emails_fetched < max_emails:
            response = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=batch_size, pageToken=page_token)
                .execute()
            )
            messages = response.get("messages", [])
            if not messages:
                logger.info("No more messages found matching the query.")
                break

            # Fetch full message details for the current batch
            batch_details = []
            for msg in messages:
                if emails_fetched >= max_emails:
                    break
                try:
                    full_msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg["id"], format="metadata")
                        .execute()
                    )
                    batch_details.append(full_msg)
                    emails_fetched += 1
                except HttpError as e:
                    logger.error(f"Failed to fetch details for message {msg['id']}: {e}")
            
            yield batch_details

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    except HttpError as e:
        logger.error(f"An error occurred while fetching email batches: {e}")


def _process_batch_for_analysis(
    batch: List[Dict[str, Any]]
) -> Tuple[Counter, Counter]:
    """
    Processes a single batch of emails to extract sender and date information.

    Args:
        batch (List[Dict[str, Any]]): A list of full email message objects.

    Returns:
        Tuple[Counter, Counter]: A tuple containing a Counter for senders and a Counter for dates.
    """
    sender_counter = Counter()
    date_counter = Counter()

    for msg in batch:
        headers = msg.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown")
        date_str = next((h["value"] for h in headers if h["name"].lower() == "date"), None)

        sender_counter[sender] += 1
        if date_str:
            try:
                # Parsing date and ignoring timezone for simplicity
                date_obj = datetime.strptime(date_str.split(' (')[0].strip(), '%a, %d %b %Y %H:%M:%S %z')
                date_counter[date_obj.strftime('%Y-%m-%d')] += 1
            except ValueError:
                logger.warning(f"Could not parse date string: {date_str}")

    return sender_counter, date_counter


def generate_sender_frequency(sender_counts: Counter, top_n: int = 50) -> Dict[str, int]:
    """
    Generates a frequency report for the most common senders.

    Args:
        sender_counts (Counter): A Counter object with sender frequencies.
        top_n (int): The number of top senders to return.

    Returns:
        Dict[str, int]: A dictionary of the top N senders and their email counts.
    """
    return dict(sender_counts.most_common(top_n))


def identify_volume_patterns(date_counts: Counter) -> Dict[str, int]:
    """
    Analyzes email volume over date ranges.

    Args:
        date_counts (Counter): A Counter object with email counts per day.

    Returns:
        Dict[str, int]: A dictionary of dates and their email volumes, sorted by date.
    """
    return dict(sorted(date_counts.items()))


def suggest_batch_strategies(sender_freq: Dict[str, int], total_emails: int) -> List[str]:
    """
    Suggests optimal batch processing strategies based on sender frequency.

    Args:
        sender_freq (Dict[str, int]): A dictionary of sender frequencies.
        total_emails (int): The total number of emails analyzed.

    Returns:
        List[str]: A list of suggested Gmail queries for batch processing.
    """
    suggestions = []
    if total_emails == 0:
        return suggestions

    # Suggest batching the most frequent senders
    for sender, count in list(sender_freq.items())[:5]:
        if count > 50:  # Only suggest for high-volume senders
            suggestions.append(f'from:"{sender}"')

    # Suggest processing by date if there are distinct patterns (placeholder logic)
    if total_emails > 1000:
        suggestions.append("before:2023/01/01") # Example suggestion
    
    return suggestions


def analyze_backlog(
    service: Resource, query: str, max_emails: int = 10000
) -> Dict[str, Any]:
    """
    Performs a full analysis of an email backlog.

    Args:
        service (Resource): Authenticated Gmail API service.
        query (str): The Gmail search query for the backlog.
        max_emails (int): The maximum number of emails to analyze.

    Returns:
        Dict[str, Any]: A dictionary containing the full analysis report.
    """
    full_sender_counts = Counter()
    full_date_counts = Counter()
    total_emails_analyzed = 0

    logger.info(f"Starting backlog analysis for query: '{query}' (max: {max_emails} emails)")

    email_generator = _fetch_emails_in_batches(service, query, max_emails)

    for batch in email_generator:
        if not batch:
            break
        
        sender_batch, date_batch = _process_batch_for_analysis(batch)
        full_sender_counts.update(sender_batch)
        full_date_counts.update(date_batch)
        total_emails_analyzed += len(batch)
        logger.info(f"Analyzed {total_emails_analyzed}/{max_emails} emails...")

    logger.info(f"Completed analysis of {total_emails_analyzed} emails.")

    sender_frequency = generate_sender_frequency(full_sender_counts)
    volume_patterns = identify_volume_patterns(full_date_counts)
    batch_suggestions = suggest_batch_strategies(sender_frequency, total_emails_analyzed)

    report = {
        "analysis_summary": {
            "total_emails_analyzed": total_emails_analyzed,
            "query": query,
            "most_frequent_sender": sender_frequency.get(next(iter(sender_frequency)), 0) if sender_frequency else "N/A",
        },
        "sender_frequency": sender_frequency,
        "volume_by_date": volume_patterns,
        "suggested_batch_queries": batch_suggestions,
    }
    return report


def export_analysis_report(report: Dict[str, Any], filename: str):
    """
    Exports the analysis report to a JSON or CSV file.

    Args:
        report (Dict[str, Any]): The analysis report from analyze_backlog.
        filename (str): The output filename (e.g., 'report.json' or 'report.csv').
    """
    file_ext = filename.split('.')[-1].lower()
    logger.info(f"Exporting analysis report to {filename}...")

    if file_ext == 'json':
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
    elif file_ext == 'csv':
        # For CSV, we flatten the structure, focusing on sender frequency
        df = pd.DataFrame.from_dict(report.get("sender_frequency", {}), orient='index', columns=['count'])
        df.index.name = 'sender'
        df.to_csv(filename)
    else:
        logger.error(f"Unsupported file format: {file_ext}. Please use 'json' or 'csv'.")
        return

    logger.info(f"Report successfully exported to {filename}.")


if __name__ == '__main__':
    """
    Example usage:
    - Authenticates using existing utility.
    - Analyzes the last 1000 unread emails.
    - Exports the report to both JSON and CSV.
    """
    from gmail_api_utils import get_gmail_service

    logging.basicConfig(level=logging.INFO)

    creds_path = '../config/credentials.json'
    token_path = '../config/token.json'
    
    gmail_service = get_gmail_service(credentials_path=creds_path, token_path=token_path)

    if gmail_service:
        # Example: Analyze up to 1000 unread emails
        analysis_report = analyze_backlog(gmail_service, query="is:unread", max_emails=1000)
        
        if analysis_report["analysis_summary"]["total_emails_analyzed"] > 0:
            export_analysis_report(analysis_report, "backlog_analysis_report.json")
            export_analysis_report(analysis_report, "sender_frequency_report.csv")
            print("Analysis complete. Reports generated.")
        else:
            print("No emails were analyzed.")