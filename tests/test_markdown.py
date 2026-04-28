from pdftranslate.markdown import ExtractedPage, render_markdown


def test_render_markdown_emits_ordered_page_headings():
    markdown = render_markdown(
        "sample.pdf",
        [
            ExtractedPage(page_number=1, text="First page text"),
            ExtractedPage(page_number=2, text="Second page text"),
        ],
    )

    assert markdown.count("## Page 1") == 1
    assert markdown.count("## Page 2") == 1
    assert markdown.index("## Page 1") < markdown.index("## Page 2")


def test_render_markdown_places_page_text_under_matching_heading():
    markdown = render_markdown(
        "sample.pdf",
        [
            ExtractedPage(page_number=1, text="First page text"),
            ExtractedPage(page_number=2, text="Second page text"),
        ],
    )

    page_1_heading = markdown.index("## Page 1")
    page_2_heading = markdown.index("## Page 2")
    first_text = markdown.index("First page text")
    second_text = markdown.index("Second page text")

    assert page_1_heading < first_text < page_2_heading
    assert page_2_heading < second_text


def test_render_markdown_preserves_source_text_without_layout_metadata():
    markdown = render_markdown(
        "source.pdf",
        [ExtractedPage(page_number=1, text="Original English sentence")],
    )

    assert "Original English sentence" in markdown
    for metadata_key in ("bbox", "x0", "y0", "x1", "y1"):
        assert metadata_key not in markdown
