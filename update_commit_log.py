import requests
import os
import json
from datetime import datetime
#import pytz


# --- Configuration ---
COMMITS_PER_REPO = 5 # Number of recent commits to fetch for each repository
OUTPUT_FILENAME = "commit_log.qmd"
INPUT_FILENAME = "repositories.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else None

if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN not set. API rate limit will be much lower.")

# --- Main Script ---
all_commits = []

# 1. Read the list of repositories
try:
    with open(INPUT_FILENAME, "r") as f:
        repos = json.load(f)
except FileNotFoundError:
    print(f"Error: {INPUT_FILENAME} not found. Run update_projects.py first.")
    exit()

# 2. Fetch commits for each repository
print(f"Found {len(repos)} repositories. Fetching commits...")
for repo_full_name in repos:
    print(f"  - Fetching for {repo_full_name}")
    url = f"https://api.github.com/repos/{repo_full_name}/commits?per_page={COMMITS_PER_REPO}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        commits = response.json()

        for commit in commits:
            all_commits.append({
                "repo": repo_full_name,
                "message": commit["commit"]["message"].split('\n')[0], # First line of message
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
                "url": commit["html_url"]
            })
    except requests.exceptions.HTTPError as e:
        print(f"    Could not fetch commits for {repo_full_name}. Status: {e.response.status_code}")
    except Exception as e:
        print(f"    An unexpected error occurred for {repo_full_name}: {e}")


# 3. Sort all collected commits by date (newest first)
all_commits.sort(key=lambda x: x["date"], reverse=True)


# 4. Write the blog-style Markdown file
print(f"\nWriting {len(all_commits)} total commits to {OUTPUT_FILENAME}...")
with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write("---\n")
    f.write('title: "Recent Commit Activity"\n\n')
    f.write("format: html\n")
    f.write('subtitle: "This site automatically tracks a curated list of GitHub projects funded by NIH grant [R01CA230551](https://reporter.nih.gov/project-details/9963159) from the National Cancer Institute to Levi Waldron at the CUNY Graduate School of Public Health and Health Policy" \n\n')
    f.write('toc: false\n')
    f.write('sidebar: false\n')
    f.write("---\n\n")
    for commit in all_commits:
        # Format date for readability
         date_obj = datetime.fromisoformat(commit['date'].replace("Z", "+00:00"))
         formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S UTC')
         #formatted_date = format_date(commit["date"])
         f.write(f"### [`{commit['repo']}`]({commit['url']})\n\n")
         f.write(f"**Message:** {commit['message']}\n\n")
         f.write(f"**Author:** {commit['author']}\n\n")
         f.write(f"**Date:** {formatted_date}\n\n")
         f.write("---\n\n")
        #f.write(f"### [`{commit['repo']}`]({commit['url']})\n\n")
        #f.write(f"**Message:** {commit['message']}\n\n")
        #f.write(f"**Author:** {commit['author']}\n\n")
        #f.write(f"**Date:** {formatted_date}\n\n")
        #f.write("---\n")

print("Done.")
