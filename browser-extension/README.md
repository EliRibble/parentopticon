# Browser Extension

In order to upload a new version:

Create a new zip with the contents (from https://extensionworkshop.com/documentation/publish/package-your-extension/)

```
zip -r -FS ../parentopticon-extension.zip * --exclude '*.git*'
```

Then log in to the Mozilla add-on workshop at https://addons.mozilla.org/en-US/developers/addons. Upload the update.
