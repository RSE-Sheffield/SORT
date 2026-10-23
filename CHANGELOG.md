# Changelog

## [0.32.0](https://github.com/RSE-Sheffield/SORT/compare/v0.31.0...v0.32.0) (2026-10-23)


### Features

* add advisory accessibility checks to CI ([#419](https://github.com/RSE-Sheffield/SORT/issues/419)) ([d9c7a75](https://github.com/RSE-Sheffield/SORT/commit/d9c7a751bf25e75c6afecea95d26eeb80a0db1cc))


### Bug Fixes

* clarify deactivate survey button as conclude survey ([#734](https://github.com/RSE-Sheffield/SORT/issues/734)) ([bf07c59](https://github.com/RSE-Sheffield/SORT/commit/bf07c5978f3bbd1328adfe9fbcac14a83a531062))
* correct grammar in Part C survey question sublabels ([#633](https://github.com/RSE-Sheffield/SORT/issues/633)) ([30bb704](https://github.com/RSE-Sheffield/SORT/commit/30bb70407dc5460982a9d3934aa90bb3a3758182))
* **survey-config:** correct wording for E3/E4 sublabels across all configs ([#563](https://github.com/RSE-Sheffield/SORT/issues/563)) ([0508809](https://github.com/RSE-Sheffield/SORT/commit/05088092f0bcf8b75e1e4463a84bbc8ce8b55449))

## [0.31.0](https://github.com/RSE-Sheffield/SORT/compare/v0.30.0...v0.31.0) (2026-10-22)


### Features

* improve multi-organisation visibility and control ([#690](https://github.com/RSE-Sheffield/SORT/issues/690)) ([#789](https://github.com/RSE-Sheffield/SORT/issues/789)) ([65ac2ea](https://github.com/RSE-Sheffield/SORT/commit/65ac2eab44bf0da841080d53e60dfe17db06a032))


### Bug Fixes

* add invitees to the organisation they were invited to ([#690](https://github.com/RSE-Sheffield/SORT/issues/690)) ([#791](https://github.com/RSE-Sheffield/SORT/issues/791)) ([6647f69](https://github.com/RSE-Sheffield/SORT/commit/6647f69f85019c9fed6644e441d58308b3138260))
* bump follow-redirects to 1.16.1 ([#787](https://github.com/RSE-Sheffield/SORT/issues/787)) ([e9cd719](https://github.com/RSE-Sheffield/SORT/commit/e9cd7190b934add5f9563a413bdca646b85aae4f))

## [0.30.0](https://github.com/RSE-Sheffield/SORT/compare/v0.29.0...v0.30.0) (2026-10-22)


### Features

* add /healthz/ health-check endpoint ([#779](https://github.com/RSE-Sheffield/SORT/issues/779)) ([bfb1557](https://github.com/RSE-Sheffield/SORT/commit/bfb155797446af2ddde3e8b468709b7d295dee81))
* configure logging and audit events ([#784](https://github.com/RSE-Sheffield/SORT/issues/784)) ([2eb4ce3](https://github.com/RSE-Sheffield/SORT/commit/2eb4ce3e5aa0825865196b7c28c65a9d60d6d430))
* email admins on production errors ([#782](https://github.com/RSE-Sheffield/SORT/issues/782)) ([aa86180](https://github.com/RSE-Sheffield/SORT/commit/aa8618074a585c47ae7e28a488db2e25633455d0))


### Bug Fixes

* require pip 26.2.2 and certifi 2026.10.19 ([#785](https://github.com/RSE-Sheffield/SORT/issues/785)) ([#786](https://github.com/RSE-Sheffield/SORT/issues/786)) ([0a9a5fa](https://github.com/RSE-Sheffield/SORT/commit/0a9a5fa77097d83478d49e9ae65cec3d77a19b90))
* serve /server-status over HTTP without redirect for collectd ([#781](https://github.com/RSE-Sheffield/SORT/issues/781)) ([01b1b02](https://github.com/RSE-Sheffield/SORT/commit/01b1b02b235216fb26dc595f0e4876f5b58e572c))

## [0.29.0](https://github.com/RSE-Sheffield/SORT/compare/v0.28.0...v0.29.0) (2026-10-20)


### Features

* add bulk research data Excel export to staff console ([#748](https://github.com/RSE-Sheffield/SORT/issues/748)) ([adbf9f8](https://github.com/RSE-Sheffield/SORT/commit/adbf9f83affabde5645ac15fc4b865061d98deeb))
* link participant information from survey detail page ([#767](https://github.com/RSE-Sheffield/SORT/issues/767)) ([40221a7](https://github.com/RSE-Sheffield/SORT/commit/40221a76df8dd24d67785cc99d89f75feeae6393))


### Bug Fixes

* remove account manager checkbox from allauth signup page ([#766](https://github.com/RSE-Sheffield/SORT/issues/766)) ([9ee07ce](https://github.com/RSE-Sheffield/SORT/commit/9ee07cea6d9e8e21bc4570a71b20a29508ad1a18))
* separate internal and research data use in participant information sheet ([#761](https://github.com/RSE-Sheffield/SORT/issues/761)) ([203d8de](https://github.com/RSE-Sheffield/SORT/commit/203d8dea34d502fdaa6d1a6cb769b8bc069d7432)), closes [#760](https://github.com/RSE-Sheffield/SORT/issues/760)


### Performance Improvements

* Idempotent virtual environment creation ([#505](https://github.com/RSE-Sheffield/SORT/issues/505)) ([a0eb3b0](https://github.com/RSE-Sheffield/SORT/commit/a0eb3b087039382b89f83cfffa46368b33960ad7))

## [0.28.0](https://github.com/RSE-Sheffield/SORT/compare/v0.27.0...v0.28.0) (2026-10-02)


### ⚠ BREAKING CHANGES

* add usage analytics console page and report command ([#739](https://github.com/RSE-Sheffield/SORT/issues/739))

### Features

* add sortable columns to console tables ([#733](https://github.com/RSE-Sheffield/SORT/issues/733)) ([18d7473](https://github.com/RSE-Sheffield/SORT/commit/18d7473d7fbdb1ba9f2a5c53f51d0a57c8b4db78))
* add usage analytics console page and report command ([#739](https://github.com/RSE-Sheffield/SORT/issues/739)) ([c50153e](https://github.com/RSE-Sheffield/SORT/commit/c50153eae0070dbdfec368b9668876ab4d803ac6))


### Bug Fixes

* allow declining research consent and fix checkbox validation ([#729](https://github.com/RSE-Sheffield/SORT/issues/729)) ([#730](https://github.com/RSE-Sheffield/SORT/issues/730)) ([851f828](https://github.com/RSE-Sheffield/SORT/commit/851f82808596bddd1010980769eea2661410ef9c))
* **deps:** bump axios to 1.20.0 and dompurify to 3.4.16 ([#751](https://github.com/RSE-Sheffield/SORT/issues/751)) ([2cf0b09](https://github.com/RSE-Sheffield/SORT/commit/2cf0b0947cfe21c1fe1afdce44d7f4917ecbc0e9))
* hide fully disabled sections and accept null for disabled fields ([#743](https://github.com/RSE-Sheffield/SORT/issues/743)) ([84d6f25](https://github.com/RSE-Sheffield/SORT/commit/84d6f25d6e9934dab3690cde6f08442ef86f2bb5))
* require login and permission to send survey invitations ([#738](https://github.com/RSE-Sheffield/SORT/issues/738)) ([#740](https://github.com/RSE-Sheffield/SORT/issues/740)) ([e4a0453](https://github.com/RSE-Sheffield/SORT/commit/e4a0453469b81a83bd954f0b57746a7ce22df87f))

## [0.27.0](https://github.com/RSE-Sheffield/SORT/compare/v0.26.0...v0.27.0) (2026-09-08)


### Features

* allow users to request to join an existing organisation ([#697](https://github.com/RSE-Sheffield/SORT/issues/697)) ([6d15913](https://github.com/RSE-Sheffield/SORT/commit/6d159130b3dd8555dfab029a444c30e5794b4aa8))
* org merge management command ([#676](https://github.com/RSE-Sheffield/SORT/issues/676)) ([#704](https://github.com/RSE-Sheffield/SORT/issues/704)) ([8dd774a](https://github.com/RSE-Sheffield/SORT/commit/8dd774ac7f58b85e5f26aaa4e3c061b4942ec476))
* switch release automation to release-please ([#709](https://github.com/RSE-Sheffield/SORT/issues/709)) ([a917c8e](https://github.com/RSE-Sheffield/SORT/commit/a917c8e67421eae5d37a25db530a99667db1f4eb))


### Bug Fixes

* combine coverage data from parallel Django test workers ([#714](https://github.com/RSE-Sheffield/SORT/issues/714)) ([60103e1](https://github.com/RSE-Sheffield/SORT/commit/60103e104ef09348e543aa86dba6da05cc71231d))
* keep the survey report rendering when responses do not match the config ([#711](https://github.com/RSE-Sheffield/SORT/issues/711)) ([304c4f4](https://github.com/RSE-Sheffield/SORT/commit/304c4f414a42346832c57b0b18f219a057839be0))
* strip ANSI colour codes when parsing svelte-check output ([#713](https://github.com/RSE-Sheffield/SORT/issues/713)) ([c6ab250](https://github.com/RSE-Sheffield/SORT/commit/c6ab250b4a723f858c527e77866f364438d469bc))
