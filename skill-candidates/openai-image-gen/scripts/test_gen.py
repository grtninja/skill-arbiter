"""Tests for write_gallery HTML escaping (fixes #12538 - stored XSS)."""

import tempfile
from pathlib import Path

import pytest

from gen import (
    get_model_defaults,
    output_file_ext,
    validate_gpt_image_2_size,
    validate_model_options,
    write_gallery,
)


def test_write_gallery_escapes_prompt_xss():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        items = [{"prompt": '<script>alert("xss")</script>', "file": "001-test.png"}]
        write_gallery(out, items)
        html = (out / "index.html").read_text()
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


def test_write_gallery_escapes_filename():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        items = [{"prompt": "safe prompt", "file": '" onload="alert(1)'}]
        write_gallery(out, items)
        html = (out / "index.html").read_text()
        assert 'onload="alert(1)"' not in html
        assert "&quot;" in html


def test_write_gallery_escapes_ampersand():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        items = [{"prompt": "cats & dogs <3", "file": "001-test.png"}]
        write_gallery(out, items)
        html = (out / "index.html").read_text()
        assert "cats &amp; dogs &lt;3" in html


def test_write_gallery_normal_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        items = [
            {"prompt": "a lobster astronaut, golden hour", "file": "001-lobster.png"},
            {"prompt": "a cozy reading nook", "file": "002-nook.png"},
        ]
        write_gallery(out, items)
        html = (out / "index.html").read_text()
        assert "a lobster astronaut, golden hour" in html
        assert 'src="001-lobster.png"' in html
        assert "002-nook.png" in html


def test_gpt_image_2_defaults_to_auto_size_and_quality():
    assert get_model_defaults("gpt-image-2") == ("auto", "auto")
    assert get_model_defaults("gpt-image-2-2026-04-21") == ("auto", "auto")


def test_gpt_image_2_rejects_transparent_background():
    with pytest.raises(ValueError, match="transparent"):
        validate_model_options(
            "gpt-image-2",
            "1024x1024",
            "high",
            "transparent",
            "",
            None,
            "",
        )


def test_gpt_image_2_accepts_current_size_constraints():
    validate_gpt_image_2_size("auto")
    validate_gpt_image_2_size("2048x1152")


def test_gpt_image_2_rejects_invalid_size_constraints():
    with pytest.raises(ValueError, match="multiples of 16"):
        validate_gpt_image_2_size("1025x1024")
    with pytest.raises(ValueError, match="3:1"):
        validate_gpt_image_2_size("3840x1024")


def test_output_compression_requires_jpeg_or_webp():
    with pytest.raises(ValueError, match="requires"):
        validate_model_options("gpt-image-2", "auto", "auto", "", "png", 50, "")


def test_gpt_image_output_extension_follows_requested_format():
    assert output_file_ext("gpt-image-2", "webp") == "webp"
    assert output_file_ext("dall-e-3", "webp") == "png"
