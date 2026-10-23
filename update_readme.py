
    items = data.get("items", [])
    if not items:
        return ""

    grouped = {}
    for item in items:
        repo_url = item.get("repository_url", "")
        repo_name = repo_url.replace(f"{GITHUB_API}/repos/", "", 1)
        if "/" not in repo_name:
            continue
        owner, repo = repo_name.split("/", 1)
        grouped.setdefault(owner, {}).setdefault(repo, []).append(item)

    output = []
    for owner, repos in grouped.items():
        output.append(f"### [{owner}](https://github.com/{owner})")
        for repo, prs in repos.items():
            repo_url = f"https://github.com/{owner}/{repo}"
            output.append(f"- **[`{repo}`]({repo_url})**")
            for pr in prs:
                number = pr.get("number")
                title = (pr.get("title") or "Merged pull request").replace("\n", " ")
                pr_url = pr.get("html_url", repo_url)
                output.append(f"  - [**#{number}**]({pr_url}) — {title}")
        output.append("")

    return "\n".join(output).strip()


def replace_marked_section(readme, start_marker, end_marker, replacement):
    """Replace the content between README marker comments."""
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if not pattern.search(readme):
        print(f"Note: markers {start_marker} / {end_marker} not found; section skipped.")
        return readme

    return pattern.sub(
        f"{start_marker}\n{replacement}\n{end_marker}",
        readme,
        count=1,
    )


def update_readme():
    readme_path = os.getenv("README_PATH", "README.md")
    print(f"Updating README for GitHub user: {USERNAME}")

    try:
        public_repos, total_stars, repos = get_github_stats(USERNAME)
    except requests.RequestException as exc:
        raise SystemExit(f"Could not fetch GitHub profile data: {exc}")

    projects_table = generate_projects_table(repos, USERNAME)
    merged_prs = get_merged_prs(USERNAME)

    with open(readme_path, "r", encoding="utf-8") as file:
        readme = file.read()

    readme = replace_marked_section(
        readme,
        "<!-- START_PROJECTS -->",
        "<!-- END_PROJECTS -->",
        projects_table,
    )

    # Only replace the open-source section if GitHub returned actual merged PRs.
    # If no merged PRs are found, keep the current section and show a clear note.
    if merged_prs:
        readme = replace_marked_section(
            readme,
            "<!-- START_OPEN_SOURCE -->",
            "<!-- END_OPEN_SOURCE -->",
            merged_prs,
        )

    # Optional dynamic stats: add these exact markers around a stats table row
    # in README.md if you want this script to update it automatically.
    stats = (
        f"| Public repositories | {public_repos} |\\n"
        f"| Stars across public repositories | {total_stars} |"
    )
    readme = replace_marked_section(
        readme,
        "<!-- START_GITHUB_METRICS -->",
        "<!-- END_GITHUB_METRICS -->",
        stats,
    )

    with open(readme_path, "w", encoding="utf-8") as file:
        file.write(readme)

    print(f"README updated successfully: {readme_path}")
    print(f"Public repositories: {public_repos} | Total stars: {total_stars}")
    print(f"Merged PRs found: {'yes' if merged_prs else 'none found'}")


if __name__ == "__main__":
    update_readme()
