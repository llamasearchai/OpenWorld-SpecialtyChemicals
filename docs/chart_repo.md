# Helm Chart Repository (GitHub Pages)

This repository can host its Helm chart via GitHub Pages.

## Enable Pages
- In GitHub settings, enable Pages for the `gh-pages` branch.
- The Chart Release workflow publishes `charts/*.tgz` and `charts/index.yaml` to `gh-pages` on tag pushes.

## Add as a Helm repo
```
helm repo add ows https://<org-or-user>.github.io/<repo>/charts
helm repo update
helm search repo ows
```

## Install from the repo
```
helm install ows ows/openworld-specialty-chemicals \
  --set image.repository=<repo> \
  --set secrets.apiToken=<token>
```
