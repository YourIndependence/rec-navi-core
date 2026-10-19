# Media access

Authenticated `GET /getSceneMasters` returns `thumbnailUrl` and `guideUrl`
alongside scene metadata. Staff, admins and owners use the same authenticated
endpoint. Raw `thumbnailUri` and `guideUri` values are not exposed.

Master image URLs use the same presigned download mechanism as recorded media.
URLs expire after 3600 seconds. Metadata responses use `Cache-Control: no-store`.
Clients can put the returned URLs in image elements and refresh the metadata
when the URLs expire. Empty, missing or null image references produce null URLs.

Only JPEG and PNG references stored in master metadata are signed. S3 URIs must
refer to `MEDIA_BUCKET_NAME`; bare object keys are resolved within that bucket.
No image bytes are transferred through the application API. URL generation does
not verify that an object exists; a missing object fails at download time.

URLs are bearer capabilities: anyone holding one can use it until expiry.
Authentication is checked when metadata is retrieved.

Before rollout, copy any existing master assets from a separate image bucket
into the configured media bucket and update their database references. Changing
configuration alone does not move objects. Frontend consumers must read the URL
fields instead of calling the proposed image-specific binary endpoints.
