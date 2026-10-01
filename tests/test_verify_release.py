import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location(
    "verify_release", Path(__file__).resolve().parents[1] / "scripts/verify-release.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="koe-tap-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.name = "koe-0.2.0-macos-arm64.zip"
        self.archive = self.directory / self.name
        self.metadata = {"isDraft": False, "isPrerelease": False, "tagName": "v0.2.0"}
        self.write_fixture()

    def write_fixture(self, entry=None):
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("koe.app/Contents/Info.plist", plistlib.dumps({
                "CFBundleIdentifier": "com.koe.dictation",
                "CFBundleShortVersionString": "0.2.0",
            }))
            if entry is not None:
                archive.writestr(entry, "fixture")
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        (self.directory / "release.json").write_text(json.dumps(self.metadata))
        (self.directory / "SHA256SUMS").write_text(f"{digest}  {self.name}\n")
        (self.directory / "koe.rb").write_text(f'''cask "koe" do
  version "0.2.0"
  sha256 "{digest}"

  url "https://github.com/YIPG/koe-releases/releases/download/v#{{version}}/koe-#{{version}}-macos-arm64.zip"
  name "koe"
  desc "Account-based menu bar dictation"
  homepage "https://koe.yuyakevinito.com/"

  depends_on arch: :arm64
  depends_on macos: ">= :ventura"

  app "koe.app"

  uninstall quit: "com.koe.dictation"
end
''')

    def test_accepts_exact_metadata_checksum_and_cask(self):
        VERIFY.verify("0.2.0", self.directory)

    def test_rejects_checksum_mismatch(self):
        (self.directory / "SHA256SUMS").write_text(f"{'0' * 64}  {self.name}\n")
        with self.assertRaisesRegex(ValueError, "checksum"):
            VERIFY.verify("0.2.0", self.directory)

    def test_rejects_executable_cask_additions(self):
        with (self.directory / "koe.rb").open("a") as cask:
            cask.write('system "echo", "unexpected"\n')
        with self.assertRaisesRegex(ValueError, "declarative"):
            VERIFY.verify("0.2.0", self.directory)

    def test_rejects_unpublished_versions(self):
        for key in ["isDraft", "isPrerelease"]:
            self.metadata[key] = True
            self.write_fixture()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "published"):
                VERIFY.verify("0.2.0", self.directory)
            self.metadata[key] = False

    def test_rejects_unsafe_archive_paths(self):
        for entry in ["../escape", "/absolute", "unrelated/file"]:
            self.write_fixture(entry)
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                VERIFY.verify("0.2.0", self.directory)

    def test_rejects_symbolic_links(self):
        entry = zipfile.ZipInfo("koe.app/Contents/Resources/link")
        entry.create_system = 3
        entry.external_attr = 0o120777 << 16
        self.write_fixture(entry)
        with self.assertRaisesRegex(ValueError, "Symbolic links"):
            VERIFY.verify("0.2.0", self.directory)


if __name__ == "__main__":
    unittest.main()
