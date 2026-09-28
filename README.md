# Yuya's Homebrew tap

Public casks for applications by [Yuya Ito](https://yuyakevinito.com/).
The koe app source is public; its website source is maintained separately.

## koe

**The first notarized release is not published yet.** There is deliberately no
placeholder cask or fabricated checksum in this repository.

After a notarized release is published and `Casks/koe.rb` is added, install with:

```sh
brew install --cask yipg/tap/koe
```

koe requires an Apple Silicon Mac running macOS 13 or later. Users provide their
own transcription API credentials; no developer API key or credits are bundled.
Homebrew may ask you to trust this third-party cask. No installation step
disables Gatekeeper or removes quarantine.

Stop dictation and quit koe before upgrading. Removing the app does not erase
your API keys or preferences; remove credentials separately in Keychain Access
if desired.

- [Website and setup](https://koe.yuyakevinito.com/)
- [Application source and releases](https://github.com/YIPG/koe)

## Maintainer: publish a verified cask

After `YIPG/koe` publishes a real notarized release:

```sh
gh workflow run update-koe.yml --repo YIPG/homebrew-tap -f version=0.2.0
```

The version above is an example, not an available release. The workflow downloads
the exact public ZIP, `SHA256SUMS`, and generated `koe.rb` from that release. It
checks the checksum and app identity/version, validates the signature and stapled
notarization ticket, assesses Gatekeeper, and exercises the resource diagnostic
before committing the cask. It rejects drafts and prereleases.

No Apple private key, API key, or cross-repository write token is needed here:
the workflow reads public release artifacts and uses this repository's own
GitHub token only to update its cask.

Test the first install, upgrade, and uninstall in an isolated app directory
before announcing availability. Update this README's status after the first
cask lands; do not advertise a working install command while `Casks/koe.rb` is
absent.
