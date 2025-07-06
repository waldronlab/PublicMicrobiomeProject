import requests
import pandas as pd
import os
import json
from html import escape

# ==============================================================================
# --- Configuration ---
# ==============================================================================
# Set the search mode. Options are: 'TOPICS', 'ORG', 'USER'
SEARCH_MODE = 'TOPICS'

# --- Search Terms ---
# For 'TOPICS' mode, provide a list of topics.
SEARCH_TOPICS = ["r01ca230551"]

# For 'ORG' mode, provide the organization's name.
SEARCH_ORG = "exampleorg"

# For 'USER' mode, provide the user's GitHub handle.
SEARCH_USER = "exampleuser"
# ==============================================================================

# --- Build the search query based on the selected mode ---
query_parts = []
title = ""
if SEARCH_MODE == 'TOPICS':
    query_parts = [f"topic:{topic}" for topic in SEARCH_TOPICS]
    title = f"Projects with Topics: {', '.join(SEARCH_TOPICS)}"
elif SEARCH_MODE == 'ORG':
    query_parts.append(f"org:{SEARCH_ORG}")
    title = f"Projects in Organization: {SEARCH_ORG}"
elif SEARCH_MODE == 'USER':
    query_parts.append(f"user:{SEARCH_USER}")
    title = f"Projects for User: {SEARCH_USER}"

search_query = "+".join(query_parts)
url = f"https://api.github.com/search/repositories?q={search_query}&per_page=100"

# --- Get data from GitHub API ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else None

if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN environment variable not set.")

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    projects = []
    repo_list_for_json = []

    for item in data["items"]:
        # Sanitize description to prevent HTML issues
        description = escape(item["description"]) if item["description"] else ""
        
        projects.append({
            # Create a clickable link for the repository name
            "Repository": f'<a href="{item["html_url"]}" target="_blank">{item["name"]}</a>',
            "Owner": item["owner"]["login"],
            "Description": description,
            "Stars": item["stargazers_count"],
            # Use 'pushed_at' for the last commit date, not 'updated_at'
            "Last Updated": item["pushed_at"].split("T")[0],
        })
        repo_list_for_json.append(item["full_name"])

    if projects:
        # --- Create HTML Page ---
        df = pd.DataFrame(projects)
        
        # Convert dataframe to an HTML table with a specific ID and classes
        table_html = df.to_html(
            index=False, 
            table_id="projectsTable", 
            classes="display compact", 
            escape=False # This allows the HTML links to be rendered
        )

        # Create the full HTML content using a template
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <!-- DataTables CSS -->
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/2.0.8/css/dataTables.dataTables.min.css">
    <style>
        body {{ font-family: sans-serif; margin: 2em; background-color: #f9f9f9; }}
        h1 {{ color: #333; }}
        .dataTables_wrapper {{ font-size: 0.9em; }}
        table.dataTable th, table.dataTable td {{ white-space: normal; }}
        table.dataTable a {{ color: #007bff; text-decoration: none; }}
        table.dataTable a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>A list of repositories discovered on GitHub. The table is sortable by clicking on headers and searchable via the search box.</p>
    
    {table_html}

    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <!-- DataTables JS -->
    <script src="https://cdn.datatables.net/2.0.8/js/dataTables.min.js"></script>

    <script>
    // Initialize the DataTable
    $(document).ready(function() {{
        $('#projectsTable').DataTable({{
            "pageLength": 25, // Show 25 entries per page
            "order": [[3, "desc"]] // Initially sort by Stars, descending
        }});
    }});
    </script>
</body>
</html>
"""
        # Write the content to an HTML file
        with open("projects.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Successfully created projects.html with {len(projects)} projects.")

        # Write the JSON file for the commit log script (no changes here)
        with open("repositories.json", "w") as f:
            json.dump(repo_list_for_json, f)
        print(f"Successfully created repositories.json.")

    else:
        print(f"No projects found for the specified criteria.")

except requests.exceptions.HTTPError as e:
    print(f"Failed to retrieve data: {e.response.status_code}")
    print(f"Response: {e.response.text}")
except Exception as e:
    print(f"An error occurred: {e}")
