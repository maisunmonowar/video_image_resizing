import os
import tempfile

import pytest

from resize_video import (
    is_video_file,
    parse_resolution,
    make_output_path,
    find_nearest_resolution,
)


def test_parse_resolution_basic():
    assert parse_resolution("720p") == 720
    assert parse_resolution("1080") == 1080
    assert parse_resolution("4k") == 4000
    assert parse_resolution("6K") == 6000
    with pytest.raises(ValueError):
        parse_resolution("not-a-res")


def test_is_video_file():
    assert is_video_file("movie.mp4")
    assert is_video_file("clip.MKV")
    assert not is_video_file("text.txt")
    assert not is_video_file("archive.zip")


def test_make_output_path():
    path = "video.mp4"
    assert make_output_path(path, height=720) == "video_720p.mp4"
    assert make_output_path(path, width=200) == "video_200w.mp4"
    assert make_output_path(path, height=720, codec="libx264") == "video_720p_libx264.mp4"
    assert make_output_path(path) == path


def test_find_nearest_resolution(tmp_path):
    # create nested structure tmp/720p/sub/any
    d1 = tmp_path / "720p"
    d2 = d1 / "sub" / "more"
    d2.mkdir(parents=True)
    assert find_nearest_resolution(str(d2), str(tmp_path)) == 720
    # directory with no resolution
    d3 = tmp_path / "nope" / "again"
    d3.mkdir(parents=True)
    assert find_nearest_resolution(str(d3), str(tmp_path)) is None

