import textwrap
import pathlib
import re

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

REPOS = "repobee/repobee repobee/repobee-junit4 KTH/spork slarse/pygitviz".split()

LANG_IMAGES = {
    path.stem.lower(): path.relative_to(CUR_DIR)
    for path in (CUR_DIR / "lang_images").iterdir()
    if path.suffix == ".svg"
}


def main():
    blog_posts = generate_blog_post_table(FEED_URL, NUM_POSTS)
    README_PATH.write_text(render_template(TEMPLATE_PATH, blog_posts), encoding="utf8")


def render_template(template_path: pathlib.Path, blog_posts: str) -> str:
    content = template_path.read_text(encoding="utf8")
    template = jinja2.Template(content)
    repos = generate_repo_table(REPOS)
    return template.render(repos=repos, blog_posts=blog_posts)


def generate_blog_post_table(feed_url: str, num_posts: int) -> str:
    raw_feed = requests.get(feed_url).content
    feed = feedparser.parse(raw_feed)
    rows = [
        [f"[{entry.title}]({entry.link})", clean_excerpt(entry.summary)]
        for entry in feed.entries[:num_posts]
    ]
    return tabulate.tabulate(rows, headers="Title Excerpt".split(), tablefmt="github")


def generate_repo_table(repos: List[str]) -> str:
    headers = "Name Description Lang Badges".split()
    repo_data = (get_repo_data(repo) for repo in repos)
    rows = [
        (
            f"[{data['name']}]({data['html_url']})",
            data["description"],
            get_language_image(data['language']),
            " ".join(
                generate_misc_badges(data) + extract_readme_badges(data["readme"])
            ),
        )
        for data in repo_data
    ]
    return tabulate.tabulate(rows, headers=headers, tablefmt="github")


def get_language_image(language: str) -> str:
    return (
        f'<img src="{LANG_IMAGES[language.lower()]}" '
        f'alt="{language}" title="{language}" width=32px/>'
    )


def generate_misc_badges(data: dict) -> List[str]:
    stars = f"![GitHub stars](https://img.shields.io/badge/%E2%AD%90-{data['stargazers_count']}-blue)"
    last_commit = f"![GitHub last commit](https://img.shields.io/github/last-commit/{data['full_name']})"
    return [stars, last_commit]


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


def get_repo_data(repo: str) -> dict:
    data = requests.get(f"https://api.github.com/repos/{repo}").json()
    data["readme"] = requests.get(
        f"https://raw.githubusercontent.com/{repo}/master/README.md"
    ).content.decode("utf8")
    return data


def clean_excerpt(text: str) -> str:
    no_tags = re.sub("<.*?>", "", text)
    no_newlines = re.sub(r"\n", " ", no_tags)
    return no_newlines


if __name__ == "__main__":
    main()
