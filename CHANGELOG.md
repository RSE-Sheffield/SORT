# Changelog

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
