import feedparser
import jinja2
import pathlib
import requests

CUR_DIR = pathlib.Path(__file__).parent
README_PATH = CUR_DIR / "README.md"
TEMPLATE_PATH = CUR_DIR / "README_TEMPLATE.md"
FEED_URL = "https://slar.se/feeds/all.atom.xml"
NUM_POSTS = 5


def main():
    blog_posts = get_blog_post_list(FEED_URL, NUM_POSTS)
    README_PATH.write_text(render_template(TEMPLATE_PATH, blog_posts), encoding="utf8")


def render_template(template_path: pathlib.Path, blog_posts: str) -> str:
    content = template_path.read_text(encoding="utf8")
    template = jinja2.Template(content)
    return template.render(blog_posts=blog_posts)


def get_blog_post_list(feed_url: str, num_posts: int) -> str:
    raw_feed = requests.get(feed_url).content
    feed = feedparser.parse(raw_feed)
    formatted_posts = "\n".join(
        [f"* [{entry.title}]({entry.link})" for entry in feed.entries[:num_posts]]
    )
    return formatted_posts


if __name__ == "__main__":
    main()
