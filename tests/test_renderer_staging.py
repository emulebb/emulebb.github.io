"""The manager can validate and stage Pages without modifying source or old evidence."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("pages_renderer", Path(__file__).parents[1] / "tools/render_pages.py")
renderer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = renderer
SPEC.loader.exec_module(renderer)


class RendererStagingTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(dir=os.environ.get("EMULEBB_WORKSPACE_OUTPUT_ROOT"))
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.workspace = self.base / "workspace"
        self.source = self.workspace / "pages"
        self.output = self.base / "output"
        self.source.mkdir(parents=True)
        self.output.mkdir()
        self.site = self.output / "artifacts/public-presence/test-run/site"
        environment = patch.dict(os.environ, {"EMULEBB_WORKSPACE_ROOT": str(self.workspace),
                                             "EMULEBB_WORKSPACE_OUTPUT_ROOT": str(self.output)})
        environment.start()
        self.addCleanup(environment.stop)

    def test_capability_probe_requires_no_environment_or_source_reads(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(renderer, "load_public_presence_contract", side_effect=AssertionError("source read")):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                self.assertEqual(renderer.main(["--capabilities"]), 0)
        self.assertEqual(json.loads(captured.getvalue()), {
            "schema": "emulebb.pages.renderer-capabilities/1",
            "outputStaging": {"protocol": 1, "boundary": "workspace-output", "sourceWrites": False}, "check": True})
        self.assertFalse(self.site.exists())

    def test_new_external_site_is_created_without_replacing_existing_evidence(self):
        self.site.parent.mkdir(parents=True)
        evidence = self.site.parent / "source-receipt.json"
        evidence.write_text("retained", encoding="utf-8")
        renderer.prepare_staging_root(self.source, self.site, self.output)
        self.assertTrue(self.site.is_dir())
        with self.assertRaisesRegex(ValueError, "already exists"):
            renderer.prepare_staging_root(self.source, self.site, self.output)
        self.assertEqual(evidence.read_text(encoding="utf-8"), "retained")

    def test_root_source_relative_and_wrong_boundary_paths_are_rejected(self):
        for destination, boundary in ((self.output, self.output), (self.source / ".local/site", self.output),
                                      (Path(".local/site"), self.output), (self.site, self.base)):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                renderer.prepare_staging_root(self.source, destination, boundary)
        self.assertFalse(self.site.exists())
        self.assertFalse((self.source / ".local").exists())

    def test_redirected_run_parent_is_refused_before_creating_any_site(self):
        redirected = self.base / "redirected"
        redirected.mkdir()
        self.site.parent.parent.mkdir(parents=True)
        try:
            self.site.parent.symlink_to(redirected, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Host cannot create this isolated directory symlink: {error}")
        with self.assertRaisesRegex(ValueError, "redirect"):
            renderer.prepare_staging_root(self.source, self.site, self.output)
        self.assertFalse((redirected / "site").exists())

    def test_source_drift_check_never_writes_rendered_content(self):
        page = self.source / "index.html"
        page.write_text("original", encoding="utf-8")
        with patch.object(renderer, "load_public_presence_contract", return_value={}), patch.object(renderer, "render_outputs", return_value={Path("index.html"): "different"}):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(renderer.main(["--root", str(self.source), "--check"]), 1)
        self.assertEqual(page.read_text(encoding="utf-8"), "original")
        self.assertFalse(self.site.exists())
