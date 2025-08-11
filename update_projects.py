import requests
import pandas as pd
from IPython.display import display
import os
import json
from html import escape
#import tabulate
#import itables
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

#--------------------Hardcode Biocondcutor url mapping -------------------------------------
HARDCODED_BIOC_URLS = {"curatedMetagenomicData" : "https://bioconductor.org/packages/curatedMetagenomicData",
"lefser" : "https://bioconductor.org/packages/lefser",
"HMP16SData" : "https://bioconductor.org/packages/HMP16SData", 
"bugsigdbr" :  "https://bioconductor.org/packages/bugsigdbr",
"MicrobiomeBenchmarkData"  : "https://bioconductor.org/packages/MicrobiomeBenchmarkData",
"bugphyzz" : "https://www.bioconductor.org/packages/release/data/experiment/html/bugphyzz.html"
}

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

#url equals github url
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
        repo_name = item["name"]
        bioconductor_link = None 
        if repo_name in HARDCODED_BIOC_URLS:
            bioconductor_url = HARDCODED_BIOC_URLS[repo_name]
            bioconductor_link = f'<a href="{bioconductor_url}" target="_blank"> </a>'
        else:
            # Attempt to construct and validate a Bioconductor URL based on naming convention
            potential_bioc_package_name = repo_name
            bioc_base_url = "https://bioconductor.org/packages/release/bioc/html/"   
            temp_bioc_url = f"{bioc_base_url}{potential_bioc_package_name}.html"
            try:
                bioc_response = requests.head(temp_bioc_url, timeout=5)
                if bioc_response.status_code == 200:
                    bioconductor_url = temp_bioc_url
                    bioconductor_link = f'<a href="{bioconductor_url}" target="_blank"> </a>'
            except requests.exceptions.RequestException as e:
               pass 
    #https://bioconductor.org/packages/release/bioc/html/bugsigdbr.html
        repo_column_html = ""
        #include bioconductor url if available and github icon
        if bioconductor_link:
            repo_column_html += f'<a href="{bioconductor_url}" target="_blank" style="color: red;">{repo_name}</a>'
        else:
            repo_column_html = f'{repo_name}'

        repo_column_html += (
        f'<a href="{item["html_url"]}" target="_blank">'
        f'<img src="githubicon.svg" style="height: 0.9em; vertical-align: middle; margin-left: 10px; margin-right: 10px">'
        f'</a>')
        if bioconductor_link:
           repo_column_html += (
            f'<a href="{bioconductor_url}" target="_blank"> </a>')

        projects.append({
            # Create a clickable link for the repository name
            "Repository": repo_column_html,
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
        html_table = df.to_html(escape=False, index=False)
        #print("xxxxx",df,"\n")
        # Write the content to an quarto markdown file
        with open("projects.qmd", "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write('title: "PublicMicrobiomeProjects with Topics: r01ca230551"\n')
            f.write('subtitle: "A list of repositories discovered on GitHub. The table is sortable by clicking on headers and searchable via the search box."\n')
            f.write("format:\n")
            f.write("  html:\n")
            #f.write("    css: style.css\n")
            f.write("    page-layout: full\n")
            f.write("    df-print: paged\n")
            f.write("---\n\n")
            f.write('<style>')
            f.write('.dataframe {\n')
            f.write('width: 100%;\n')
            f.write('border-collapse: collapse;\n')
            f.write('margin-top: 20px;\n')
            f.write('}\n') 
            f.write('.dataframe th, .dataframe td {\n')
            f.write('border: 1px solid #ddd;\n')
            f.write('padding: 8px;\n')
            f.write('text-align: left;\n')
            f.write('}\n') 
            f.write('.dataframe th {\n')
            f.write('background-color: #f2f2f2;\n')
            f.write('cursor: pointer;\n')
            f.write('}\n')
            f.write('</style>\n\n')
            f.write('<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css"> \n\n')
            f.write(html_table)
            f.write('\n\n')
            f.write('<script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.6.0.min.js"></script> \n')
            f.write('<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script> \n')
            f.write('<script>\n')
            f.write('$(document).ready( function () { \n')
            f.write("$('.dataframe').DataTable();\n")
            f.write('} );\n')
            f.write('</script> \n')  
        print(f"Successfully created projects.qmd with {len(projects)} projects.")

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
