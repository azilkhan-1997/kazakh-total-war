# Microsoft VC runtime: free licensing route, not yet established for this publisher

Checked 2026-11-08 against Microsoft's current license directory, actual linked DOCX agreements, and redistribution documentation. No software license was accepted, installation performed, or entitlement attributed to SAYRAM PLANETA HOLDING during this research.

## Practical finding

A paid Visual Studio purchase is **not intrinsically necessary** for an OSI-licensed open-source game. Visual Studio Community provides an explicit route. A public VC runtime download alone does not establish redistribution rights. The current record therefore remains **unresolved entitlement**, with a concrete free route rather than a presumed commercial-license expense.

| Primary source | Verified result |
|---|---|
| [Community 2026 actual agreement](https://visualstudio.microsoft.com/wp-content/uploads/2025/10/Visual_Studio_2026-License-Community_ENU.docx), updated 2025-10-01 | Organizational users may develop/test OSI-licensed open-source applications without the ordinary five-user restriction; the enterprise exception expressly preserves those uses. The agreement also grants distribution of listed object code within developed applications. |
| [2026 REDIST list](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution), updated 2025-11-11 | A valid license to a listed Visual Studio edition is required. The list expressly includes Community and Build Tools. Unmodified VC runtime files/package may accompany the program, subject to its license. The download-site package is identified as the same package. Debug runtime directories and preview files are excluded. |
| [Microsoft deployment documentation](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170), updated 2026-04-15 | Package, merge-module, and individual-binary redistribution is limited to licensed Visual Studio users. Microsoft recommends installing the official prerequisite package. |

Community wording includes “applications released under Open Source Initiative (OSI) approved open source software licenses” and “you may distribute in applications you develop”. These are the sole quotations from that agreement here (20 words combined).

Community distribution conditions include adding substantial application functionality; preserving protection of Microsoft's component in distributor/end-user terms; the stated indemnity; no preview/Insiders-dependent distribution; no implied Microsoft endorsement; and no relicensing Microsoft's source under an excluded license. Keep Microsoft components separate and unmodified, with their own notices/terms. The game's GPL status does not relicense Microsoft's files.

## Build Tools alone is not the clean route

The [actual Build Tools 2026 agreement](https://visualstudio.microsoft.com/wp-content/uploads/2025/10/Visual_Studio_2026-License-Diagnostic_and_Build_Tools_ENU.docx) generally requires a valid Community/Professional/Enterprise license. Without one, it separately permits building third-party OSI-licensed C++ dependencies required by an application. That exception allows only minor compilation-related changes, not general dependency development/testing.

Crucially, this downloaded agreement contains no Distributable Code section and its scope restricts redistribution. Although the REDIST page names Build Tools, it makes that listing subject to the applicable agreement. Do not treat installing Build Tools alone, its dependency exception, an existing Windows SDK, or availability on a hosted runner as established publisher redistribution entitlement. Community's explicit grant avoids relying on this unresolved discrepancy.

The [standalone V14 runtime agreement](https://visualstudio.microsoft.com/wp-content/uploads/2025/10/Visual-C-V14-License-Redistributable_and_Runtime_ENU.docx) permits installation/use but restricts redistribution. It is an end-user license, not a substitute for the developer distribution grant.

## Concrete close-out evidence

An authorized developer/publisher must actually obtain/use the eligible stable Community product under its terms and preserve that license record; this research does not do so on their behalf. Record edition/version, responsible licensee, qualifying open-source project and acceptance/acquisition evidence, plus the exact runtime package/version/hash and applicable REDIST entry. Using an owned Windows build machine is the straightforward documented path; remote build-device permissions have additional ownership/hosting/control conditions.

The distribution clause does **not expressly demand recompiling every pre-existing engine binary** with Community. Do not invent that requirement. A real eligible development/build workflow provides clearer evidence than a nominal install solely asserted as clearance.

After entitlement is established: bundle the unmodified release VC runtime package, preserve its terms and installer handling, and test installation and first launch on clean offline Windows. Separate debug DLLs require their own permitted redistribution basis or removal/rebuild; Community acquisition does not authorize `debug_nonredist` content.

## Evidence files

The three downloaded original DOCX files, extracted text, source URLs, byte sizes and SHA-256 hashes are alongside this report. `provenance.json` records the exact retrieved bytes. These establish what was inspected, not publisher acceptance or clearance of all other runtime dependencies.
