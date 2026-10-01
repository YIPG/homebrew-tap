#!/usr/bin/env python3
"""Validate release metadata and the generated cask before importing it."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import re
import stat
import sys
import zipfile


def verify(version, directory):
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ValueError("Use MAJOR.MINOR.PATCH.")
    directory = Path(directory)
    metadata = json.loads((directory / "release.json").read_text())
    if metadata["isDraft"] or metadata["isPrerelease"] or metadata["tagName"] != f"v{version}":
        raise ValueError("Require a published, non-prerelease version.")
    name = f"koe-{version}-macos-arm64.zip"
    archive = directory / name
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    checksum = digest.hexdigest()
    if (directory / "SHA256SUMS").read_text().split() != [checksum, name]:
        raise ValueError("Release checksum does not match the exact ZIP.")
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe archive path.")
            if not path.parts or path.parts[0] not in ["koe.app", "__MACOSX"]:
                raise ValueError("Unexpected top-level release content.")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Symbolic links are not expected in this static application bundle.")
        info = plistlib.loads(bundle.read("koe.app/Contents/Info.plist"))
        if info.get("CFBundleIdentifier") != "com.koe.dictation" or info.get("CFBundleShortVersionString") != version:
            raise ValueError("Unexpected app identity or version.")
    cask = (directory / "koe.rb").read_text()
    # Import only the expected declarative cask, not arbitrary release-supplied Ruby.
    expected = f'''cask "koe" do
  version "{version}"
  sha256 "{checksum}"

  url "https://github.com/YIPG/koe-releases/releases/download/v#{{version}}/koe-#{{version}}-macos-arm64.zip"
  name "koe"
  desc "Account-based menu bar dictation"
  homepage "https://koe.yuyakevinito.com/"

  depends_on arch: :arm64
  depends_on macos: ">= :ventura"

  app "koe.app"

  uninstall quit: "com.koe.dictation"
end
'''
    if cask != expected:
        raise ValueError("The release cask differs from the reviewed declarative template.")
    print(f"Verified metadata and SHA-256 for {name}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: verify-release.py VERSION DOWNLOAD_DIRECTORY")
    try:
        verify(sys.argv[1], sys.argv[2])
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, plistlib.InvalidFileException) as error:
        sys.exit(f"Release validation failed: {error}")
