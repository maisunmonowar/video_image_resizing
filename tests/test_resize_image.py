import os
import tempfile

import pytest

from resize_image import (
    is_image_file,
    parse_resolution,
    parse_dimension,
    make_output_path,
    find_nearest_resolution,
    process_file,
)
from PIL import Image


def test_is_image_file():
    assert is_image_file("photo.jpg")
    assert is_image_file("clip.PNG")
    assert not is_image_file("video.mp4")


def test_parse_resolution_and_dimension():
    assert parse_resolution("720p") == 720
    assert parse_resolution("6K") == 6000
    with pytest.raises(ValueError):
        parse_resolution("foo")

    assert parse_dimension("800x600") == (800, 600)
    assert parse_dimension("720p") == (None, 720)
    with pytest.raises(ValueError):
        parse_dimension("12xabc")


def test_make_output_path():
    path = "img.png"
    assert make_output_path(path, width=100) == "img_100w.png"
    assert make_output_path(path, height=200, quality=75) == "img_200p_q75.png"
    assert make_output_path(path) == path


def test_process_file(tmp_path, monkeypatch):
    # create a simple image
    img_path = tmp_path / "test.jpg"
    Image.new("RGB", (100, 100), color="red").save(img_path)
    out = tmp_path / "test_50p.jpg"
    process_file(str(img_path), height=50, dry_run=False)
    assert out.exists()
    with Image.open(out) as im:
        assert im.size[1] == 50


def test_find_nearest_resolution(tmp_path):
    d1 = tmp_path / "300"
    d2 = d1 / "inside"
    d2.mkdir(parents=True)
    assert find_nearest_resolution(str(d2), str(tmp_path)) == 300
    d3 = tmp_path / "nomatch" / "sub"
    d3.mkdir(parents=True)
    assert find_nearest_resolution(str(d3), str(tmp_path)) is None
