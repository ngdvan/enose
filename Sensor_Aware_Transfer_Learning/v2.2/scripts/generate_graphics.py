"""Regenerate full-revision Figures 3 and 4 from the completed evidence."""
from build_full_revision_docx import OUT, figures


if __name__ == '__main__':
    figures()
    print(f'Graphics written to {OUT / "figures"}')
