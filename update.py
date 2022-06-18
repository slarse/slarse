import pathlib
import re
import datetime

from typing import List

import tabulate
import feedparser
import jinja2
import requests

CUR_DIR = pathlib.Path(__file__).parent
README_PATH = CUR_DIR / "README.md"
TEMPLATE_PATH = CUR_DIR / "README_TEMPLATE.md"
FEED_URL = "https://slar.se/feeds/all.atom.xml"
NUM_POSTS = 5

REPOS = "repobee/repobee inria/spoon KTH/spork slarse/rusthon slarse/pygitviz SpoonLabs/sorald".split()
USER = "slarse"


def main():
    blog_posts = generate_blog_post_table(FEED_URL, NUM_POSTS)
    README_PATH.write_text(render_template(TEMPLATE_PATH, blog_posts), encoding="utf8")


def render_template(template_path: pathlib.Path, blog_posts: str) -> str:
    content = template_path.read_text(encoding="utf8")
    template = jinja2.Template(content)
    repos = generate_repo_table(REPOS, USER)
    return template.render(repos=repos, blog_posts=blog_posts)


def generate_blog_post_table(feed_url: str, num_posts: int) -> str:
    raw_feed = requests.get(feed_url).content
    feed = feedparser.parse(raw_feed)
    rows = [
        [f"[{entry.title}]({entry.link})", clean_excerpt(entry.summary)]
        for entry in feed.entries[:num_posts]
    ]
    return tabulate.tabulate(rows, headers="Title Excerpt".split(), tablefmt="github")


def generate_repo_table(repos: List[str], user: str) -> str:
    headers = ["Repo", "Description", "Language", "Stars", "My Contributions"]
    repo_data = (get_repo_data(repo, user) for repo in repos)

    def create_commits_badges(data: dict) -> str:
        return f"{create_commits_badge(data)} {create_commits_30_days_badge(data)}"

    rows = [
        (
            f"[{data['name']}]({data['html_url']})",
            data["description"],
            data["language"],
            create_stargazers_badge(data),
            create_commits_badges(data),
        )
        for data in repo_data
    ]
    return tabulate.tabulate(rows, headers=headers, tablefmt="github")


def create_commits_30_days_badge(data: dict) -> List[str]:
    monthly_commits_badge = (
        f"![My commits past 30 days]"
        f"(https://img.shields.io/badge/%23commits%20(30%20days)-"
        f"{data['num_monthly_commits']}-blue)"
    )
    return f"[{monthly_commits_badge}]({data['monthly_commits_web_url']})"


def create_commits_badge(data: dict) -> List[str]:
    commits_badge = (
        f"![My commits]"
        f"(https://img.shields.io/badge/%23commits-"
        f"{data['contributions']}-blue)"
    )
    return f"[{commits_badge}]({data['commits_web_url']})"


def create_stargazers_badge(data: dict) -> str:
    stars_badge = (
        f"![GitHub stars](https://img.shields.io/badge/%E2%AD%90-"
        f"{data['stargazers_count']}-blue)"
    )
    return f"[{stars_badge}]({data['stargazers_web_url']})"


def extract_readme_badges(readme: str) -> List[str]:
    badge_keywords = ["build status", "coverage", "license"]
    return [
        match.group()
        for key in badge_keywords
        if (
            match := re.search(
                rf"^[\[!].*?{key}\].*$", readme, flags=re.IGNORECASE | re.MULTILINE
            )
        )
    ]


def get_repo_data(repo: str, user: str) -> dict:
    repo_api_url = f"https://api.github.com/repos/{repo}"
    data = requests.get(repo_api_url).json()
    data["readme"] = requests.get(
        f"https://raw.githubusercontent.com/{repo}/master/README.md"
    ).content.decode("utf8")

    thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)
    monthly_commits_api_url = (
        f"{repo_api_url}/commits?author={user}&since={thirty_days_ago}"
    )
    monthly_commits_web_url = (
        f"https://github.com/{repo}/commits?author={user}&since={thirty_days_ago}"
    )
    monthly_commits = requests.get(monthly_commits_api_url).json()
    data["num_monthly_commits"] = len(monthly_commits)
    data["monthly_commits_web_url"] = monthly_commits_web_url

    data["stargazers_web_url"] = f"https://github.com/{repo}/stargazers"
    data["commits_web_url"] = f"https://github.com/{repo}/commits?author={user}"
    data["contributions"] = get_contributions(repo, user)

    return data


def get_contributions(repo: str, user: str) -> int:
    match = None
    page = 1
    while not match:
        contributors = requests.get(
            f"https://api.github.com/repos/{repo}/contributors?page={page}"
        ).json()
        if not contributors:
            raise ValueError(f"{user} has no contributions in {repo}")

        match = next(filter(lambda entry: entry["login"] == user, contributors), {})
        page += 1

    return match["contributions"]


def clean_excerpt(text: str) -> str:
    no_tags = re.sub("<.*?>", "", text)
    no_newlines = re.sub(r"\n", " ", no_tags)
    return no_newlines


if __name__ == "__main__":
    main()
