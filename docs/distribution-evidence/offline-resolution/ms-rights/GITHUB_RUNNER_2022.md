# GitHub-hosted Windows 2022: build service versus distribution entitlement

Checked 2026-11-08. No installation, license acceptance, build execution or upload was performed by this audit.

## Positive primary evidence for the proposed CI workflow

| Evidence | What it establishes |
|---|---|
| [GitHub runner selection documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job) | Standard `windows-2022` jobs are offered without runner-minute charges for public repositories; currently listed as 4 CPU, 16 GB RAM, 14 GB SSD. |
| [GitHub-hosted runner documentation](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners) | GitHub supplies maintained VMs with preinstalled development tools and recommends using those tools in workflows. The actual run's `Set up job` log identifies the precise image/software list. |
| [Current Windows 2022 image manifest](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md) | The inspected manifest identifies image `20261101.353.1`, with Visual Studio Enterprise 2022 `17.14.37827.9` installed under `C:\Program Files\Microsoft Visual Studio\2022\Enterprise`. This is availability evidence, not an individual publisher license certificate. |
| [GitHub additional product terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features), effective 2026-08-27, Actions section | Actions is expressly provided for application development/testing; workflows must relate to the repository's software project. It is not a free general-purpose hosting/CDN service. |

**Assessment:** compiling and testing the repository's open-source engine is the advertised GitHub Actions use case. The documented service availability supports an ordinary CI validation workflow. It does not by itself establish a separate Visual Studio Enterprise full-use license for SAYRAM PLANETA HOLDING, or rights to extract/repackage Microsoft DLLs.

## Exact agreement and the unresolved distinction

The [actual VS 2022 Enterprise/Professional/Trial agreement](https://visualstudio.microsoft.com/wp-content/uploads/2021/11/Visual-Studio-2022-Enterprise-Professional-License-EN.docx), linked by [Microsoft's license directory page](https://visualstudio.microsoft.com/license-terms/vs2022-ga-proenterprise/), distinguishes trial rights from full-use rights. Trial use is limited to internal evaluation, with production distribution/deployment restrictions. Full-use §4(b) describes build-device use, and §5 contains the Distributable Code grant and requirements. The local original, extracted text and hash are saved as `enterprise2022.*` and `enterprise2022-provenance.json`.

The inspected public GitHub terms do not expressly grant an individual Visual Studio Enterprise subscription or sublicense Microsoft runtime redistribution to the repository owner. They also do not say every standard Actions user must separately purchase Enterprise. Neither conclusion should be invented. A generic retail trial agreement cannot establish which service-specific arrangement GitHub has for its managed images.

The runner-images discussion [#7233](https://github.com/actions/runner-images/discussions/7233) contains a licensing opinion by a community participant; it is **not** treated here as an authoritative Microsoft/GitHub grant. Reports of trial-expiry errors are activation observations, not proof of the legal basis for the hosted service.

## Boundaries for implementation and reporting

- Label successful output accurately: **compiled/tested on GitHub-hosted Windows 2022**, with image ID, compiler version and logs. Do not relabel that as publisher Microsoft redistribution clearance.
- For an initial validation run, retain build/test diagnostics and hashes; do not indiscriminately upload the runner's SDK, compiler, `VC\Redist` folders or a bundled runtime tree.
- A CI artifact download is still a transfer of files. The word “artifact” does not exempt Microsoft components from their license. Publishing a complete installer requires the separate runtime entitlement and component notices already identified in `RESOLUTION.md`.
- A concrete free publisher route remains eligible Community licensing for this public GPL project. That license does not automatically transform the preinstalled Enterprise IDE into a Community installation.

No paid-tool requirement was established by this audit. The unresolved item is the publisher's documented distribution basis, not the availability of a free Windows CI service.
