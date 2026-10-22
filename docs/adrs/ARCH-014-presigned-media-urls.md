---
id: ARCH-014
title: Presigned URLs for Stored Media Delivery
domain: backend
status: active
date: 2026-10-22
rules: false
files:
  - 'src/recnavi/core/types/**/*.py'
  - 'src/recnavi/core/storage/**/*.py'
  - 'src/recnavi/core/scene/**/*.py'
  - 'src/recnavi/core/project/**/*.py'
  - 'src/recnavi/application/**/*.py'
  - 'src/recnavi/apis/**/*.py'
---

## Context

The client shows stored media: scene master example and guide images, template
tile images, project scene videos and thumbnails, and the project archive
download. Browser `<img src>` and `<video src>` elements cannot send an
Authorization header, so a protected API endpoint cannot be used directly as a
media source. Streaming bytes through the API is also constrained by the API
Gateway 10MB response limit.

The first design of the scene master change (PR #59) added a streaming endpoint
per asset (`getSceneThumbnail`, later `getTemplateThumbnail`). During review
the reviewer asked to settle one design: a separate API per asset, one generic
`getSource` style API, or presigned URLs. The reviewer also proposed turning
the response type into the domain type with an `.attach_presigned_url()` method
instead of keeping duplicated `Hoge` / `HogeView` types, and asked that the
settled design be recorded in an ADR. This is that ADR.

## Decision

All stored media is exposed as temporary presigned URLs inside the normal API
responses. There are no per-asset or generic streaming endpoints for media.

- Domain types in `core/types/` hold durable storage references
  (`thumbnail_uri`, `guide_uri`, `video_key`, `thumbnail_key`; declared with
  `Field(exclude=True)`) and URL fields (`thumbnail_url`, `guide_url`,
  `video_url`, `download_url`). The reference fields are never serialized to
  the client; the URL fields are never persisted.
- `SceneMaster`, `ScenesTemplate`, `Scene`, and `Project` each expose
  `async attach_presigned_url(self, *, storage: BaseObjectStorage) -> Self`.
  It fills the URL fields of the instance in place and returns `self`.
  `Project.attach_presigned_url()` delegates to every child `Scene`. This
  method is the single place that converts storage references into URLs.
- Master and template references go through
  `core/storage/image_urls.py:generate_image_url`. It returns `None` for an
  empty reference, accepts either a bare object key or an `s3://` URI, and
  raises `ClientUnprocessableEntityError` when the URI scheme is not `s3`, the
  bucket is not `MEDIA_BUCKET_NAME`, a query or fragment is present, or the
  extension is not `.jpg`, `.jpeg`, or `.png`. It then calls
  `BaseObjectStorage.generate_presigned_url`.
- Scene videos and thumbnails use `storage.generate_presigned_url` directly in
  `Scene.attach_presigned_url` (keys are written by the application, not given
  by users; missing keys yield `None`).
- Expiry is 3600 seconds: `MEDIA_URL_EXPIRATION_SECONDS` (masters, templates),
  `SCENE_URL_EXPIRATION_SECONDS` (scene media), and
  `DOWNLOAD_URL_EXPIRATION_SECONDS` (archive). URLs are regenerated on every
  call and existence of the object is not checked.
- A single media bucket, `MEDIA_BUCKET_NAME`, serves all media. The separate
  `SCENE_IMAGES_BUCKET_NAME` was dropped, and `S3Client` is created once in
  `main.py` with that bucket.
- Where it is called: `application/` use cases (`get_project`, `get_projects`,
  `get_templates`, `get_scene_masters`, `update_scene_master`) and the `core/`
  operations that return a project (`update_project`, `update_scene`,
  `review_scene`) call `attach_presigned_url(storage=storage)` as the last step,
  after authorization and filtering. Routers do not sign URLs and set
  `Cache-Control: no-store` on list endpoints that carry them. Concrete S3
  access stays in `infrastructure/s3/`.
- Persistence uses the explicit `to_storage_item()`, which writes the durable
  references and omits the URL fields (see ARCH-002).
- The project archive is created on demand by `Project.create_download_url()`
  (`downloadProject`) and returned as a presigned `download_url`. It is not a
  side effect of listing or URL attachment.
- One type serves both persistence and responses. Do not define `HogeView` only
  to add temporary URLs. Types with a genuinely different contract (for example
  the privacy-limited `UserSummary`) stay separate.

## Rationale

Presigned URLs let the browser fetch media directly from object storage with
no Authorization header and without passing bytes through API Gateway or the
application, so the 10MB limit does not apply. Access is still gated: a URL is
only produced after the normal authenticated and authorized API call, and it
expires. Putting URLs in the existing responses removes extra round trips and
extra endpoints, and keeps the design uniform for images, videos, and archives.
Centralizing conversion in one method on the domain type keeps URL rules out
of routers and avoids a duplicate response type that must track every field.

## Consequences

- **Positive**: No media streaming endpoints; fewer routes to authorize and
  document.
- **Positive**: One type per concept; field changes happen in one place.
- **Positive**: Bytes flow directly from object storage to the client.
- **Negative**: A URL is a bearer link until it expires; anyone holding it can
  fetch the object for up to one hour. Responses must not be cached
  (`Cache-Control: no-store`).
- **Negative**: Clients must refetch the resource when a URL expires.
- **Negative**: Every code path that returns a media-bearing type must remember
  to call `attach_presigned_url`; there is no Archgate rule for this
  (`rules: false`), so review and tests enforce it.
- **Negative**: Because the method mutates and returns `self`, callers needing
  the unsigned object must copy it before attaching.
- **Note**: `download_object_stream` remains in the storage interface only as
  an internal helper of archive building; it is not exposed as an endpoint.
  Listing scene masters and templates still uses `scan`; the reviewer noted
  this could be a query on the table key, which is unrelated to this decision.

## Alternatives Considered

- **A separate API per asset** (`getSceneThumbnail`, `getTemplateThumbnail`,
  ...)
  - **Positive**: Simple to authorize per request.
  - **Negative**: One endpoint and one round trip per asset; N+1 images in a
    list; bytes pass through the API and the 10MB limit; the earlier endpoint
    for staff was also placed in the wrong router.
- **One generic `getSource` API**
  - **Positive**: One endpoint instead of many.
  - **Negative**: Still streams through the API and the same size limit; needs
    its own key-based authorization for arbitrary objects; still needs one
    request per asset.
- **`Hoge` / `HogeView` duplicate types**
  - **Positive**: Response schema is isolated from the persistence type.
  - **Negative**: Duplicated fields that drift, unions for nested aggregates,
    and conversion code at every call site.

## Compliance

**Do:**
- Return stored media only as presigned URLs inside regular API responses.
- Put new media fields on the existing domain type as an excluded reference
  plus a URL field, and fill the URL in `attach_presigned_url(storage=...)`.
- Call `attach_presigned_url` after authorization, before returning, from
  `application/` or `core/` operations.
- Validate `s3://` references through `generate_image_url`, and use the single
  `MEDIA_BUCKET_NAME` bucket.
- Persist with `to_storage_item()` so URLs are never stored.
- Add a test that a new media-bearing response contains URLs and no
  references.

**Don't:**
- Add endpoints that stream or proxy stored media bytes.
- Add a `HogeView` type only to carry temporary URLs.
- Generate presigned URLs in routers or in `infrastructure/`, or hardcode
  expiry values at call sites.
- Return `*_uri` / `*_key` storage references to the client.
- Add another media bucket setting.

## References

- PR #59: https://github.com/YourIndependence/rec-navi-core/pull/59
- ARCH-001: Clean Architecture (layer responsibilities)
- ARCH-002: Pydantic-First Type System (media models and temporary URLs)
- ARCH-013: Project Authorization Pattern (authorize before attaching URLs)
