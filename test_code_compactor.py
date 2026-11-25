import subprocess
import tempfile
import unittest
from pathlib import Path

import code_compactor


def initialize_repository(root):
    subprocess.run(
        ["git", "init", str(root)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def track_files(root, *paths):
    subprocess.run(
        ["git", "add", "--", *paths],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class CodeCompactorTests(unittest.TestCase):
    def test_collects_only_tracked_readme_source_and_test_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            initialize_repository(root)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_main.py").write_text(
                "def test_main(): pass\n", encoding="utf-8"
            )
            (root / "untracked.py").write_text(
                "this_file_is_not_tracked = True\n", encoding="utf-8"
            )
            track_files(root, "README.md", "main.py", "tests/test_main.py")

            paths = code_compactor.collect_files(root)

            self.assertEqual(
                ["README.md", "main.py", "tests/test_main.py"],
                [path.relative_to(root).as_posix() for path in paths],
            )

    def test_document_uses_longer_fence_if_content_contains_backticks(self):
        document = code_compactor.fenced_block('print("```")\n', "python")

        self.assertIn('````python\nprint("```")\n````', document)

    def test_each_run_creates_a_new_reference_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "project"
            root.mkdir()
            initialize_repository(root)
            source = root / "main.py"
            source.write_text("print('first')\n", encoding="utf-8")
            track_files(root, "main.py")
            requested_output = base / "reference.md"

            first_output, count = code_compactor.write_reference(
                root, requested_output
            )
            source.write_text("print('second')\n", encoding="utf-8")
            second_output, second_count = code_compactor.write_reference(
                root, requested_output
            )

            self.assertEqual(requested_output.resolve(), first_output)
            self.assertEqual(base / "reference_2.md", second_output)
            self.assertEqual(1, count)
            self.assertEqual(1, second_count)
            self.assertIn("print('first')", first_output.read_text(encoding="utf-8"))
            self.assertIn("print('second')", second_output.read_text(encoding="utf-8"))

    def test_rejects_output_inside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)

            with self.assertRaisesRegex(ValueError, "outside the project"):
                code_compactor.write_reference(root, root / "reference.md")

    def test_rejects_non_repository_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Not inside a Git repository"):
                code_compactor.collect_files(directory)


if __name__ == "__main__":
    unittest.main()
