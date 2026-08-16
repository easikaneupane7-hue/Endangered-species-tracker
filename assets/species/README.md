# Private species images

Store species photos in this folder. The application only displays image files located under `assets/`, and never downloads images from Google Drive or any website.

In the Google Sheet, enter a relative path such as:

```text
assets/species/bengal-tiger.jpg
```

Do not use `http://`, `https://`, `file://`, or an absolute path. Remote and out-of-folder paths are intentionally rejected.
