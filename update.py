import pathlib
import jinja2

CUR_DIR = pathlib.Path(__file__).parent
README_PATH = CUR_DIR / "README.md"
TEMPLATE_PATH = CUR_DIR / "README_TEMPLATE.md"


def main():
    README_PATH.write_text(render_template(TEMPLATE_PATH), encoding="utf8")


def render_template(template_path: pathlib.Path) -> str:
    content = template_path.read_text(encoding="utf8")
    template = jinja2.Template(content)
    return template.render(name="Simon")


if __name__ == "__main__":
    main()
