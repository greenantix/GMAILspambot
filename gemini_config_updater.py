import argparse
import json
import os
import sys

from log_config import init_logging, get_logger

SETTINGS_PATH = "settings.json"

def load_settings(settings_path):
    with open(settings_path, "r") as f:
        return json.load(f)

def save_settings(settings, settings_path):
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2, sort_keys=False)

def load_gemini_output(path):
    with open(path, "r") as f:
        return json.load(f)

def update_label_schema(label_schema, logger):
    # Stub Gmail API calls
    for label in label_schema.get("create", []):
        logger.info(f"TODO: Create label '{label}' via Gmail API (stubbed).")
        # TODO: Implement Gmail API label creation

    for label in label_schema.get("delete", []):
        logger.info(f"TODO: Delete label '{label}' via Gmail API (stubbed).")
        # TODO: Implement Gmail API label deletion

    for old, new in label_schema.get("rename", {}).items():
        logger.info(f"TODO: Rename label '{old}' to '{new}' via Gmail API (stubbed).")
        # TODO: Implement Gmail API label renaming

def update_category_rules(category_rules, rules_dir, logger):
    if not os.path.exists(rules_dir):
        os.makedirs(rules_dir)
    for label, rule in category_rules.items():
        rule_path = os.path.join(rules_dir, f"{label}.json")
        try:
            with open(rule_path, "w") as f:
                json.dump(rule, f, indent=2)
            logger.info(f"Updated rule for label '{label}' at {rule_path}")
        except Exception as e:
            logger.error(f"Failed to write rule for label '{label}': {e}")

def update_auto_operations(auto_ops, rules_dir, logger):
    # Write auto-operations to a dedicated file
    auto_ops_path = os.path.join(rules_dir, "auto_operations.json")
    try:
        with open(auto_ops_path, "w") as f:
            json.dump(auto_ops, f, indent=2)
        logger.info(f"Updated auto-operations at {auto_ops_path}")
    except Exception as e:
        logger.error(f"Failed to write auto-operations: {e}")

def update_label_action_mappings(settings, category_rules, logger):
    updated = False
    if "label_action_mappings" not in settings:
        settings["label_action_mappings"] = {}
    for label, rule in category_rules.items():
        action = rule.get("action")
        if action and settings["label_action_mappings"].get(label) != action:
            logger.info(f"Mapping label '{label}' to action '{action}' in settings.")
            settings["label_action_mappings"][label] = action
            updated = True
    return updated

def main():
    parser = argparse.ArgumentParser(description="Update system config/rules from Gemini output JSON.")
    parser.add_argument("--gemini-output", type=str, help="Path to Gemini output JSON file.")
    parser.add_argument("--settings", type=str, default=SETTINGS_PATH, help="Path to settings.json.")
    args = parser.parse_args()

    # Load settings
    try:
        settings = load_settings(args.settings)
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize logging
    log_dir = settings.get("paths", {}).get("logs", "logs")
    init_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    # Determine Gemini output path
    gemini_output_path = args.gemini_output
    if not gemini_output_path:
        logger.error("No Gemini output file specified. Use --gemini-output.")
        sys.exit(1)

    # Load Gemini output
    try:
        gemini = load_gemini_output(gemini_output_path)
    except Exception as e:
        logger.error(f"Failed to load Gemini output: {e}")
        sys.exit(1)

    # Update label schema (stub Gmail API)
    try:
        update_label_schema(gemini.get("label_schema", {}), logger)
    except Exception as e:
        logger.error(f"Error updating label schema: {e}")

    # Update category rules
    rules_dir = settings.get("paths", {}).get("rules", "rules")
    try:
        update_category_rules(gemini.get("category_rules", {}), rules_dir, logger)
    except Exception as e:
        logger.error(f"Error updating category rules: {e}")

    # Update auto-operations
    try:
        update_auto_operations(gemini.get("auto_operations", {}), rules_dir, logger)
    except Exception as e:
        logger.error(f"Error updating auto-operations: {e}")

    # Update label_action_mappings in settings
    try:
        updated = update_label_action_mappings(settings, gemini.get("category_rules", {}), logger)
        if updated:
            save_settings(settings, args.settings)
            logger.info(f"Updated label_action_mappings in {args.settings}")
    except Exception as e:
        logger.error(f"Error updating label_action_mappings: {e}")

    logger.info("Gemini config update complete.")

if __name__ == "__main__":
    main()