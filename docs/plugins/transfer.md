# Transfer plugins

Transfer plugins move files between the controller and the remote target over the
active SSH connection.

## `transfer.upload`

Uploads a local file or directory to the remote target.

```yaml
- id: upload_release
  use: transfer.upload
  with:
    src: ./dist/myapp.tar.gz
    dest: /tmp/myapp.tar.gz
```

## `transfer.download`

Downloads a remote file or directory to the controller.

```yaml
- id: collect_log
  use: transfer.download
  with:
    src: /var/log/myapp/app.log
    dest: ./artifacts/{{ server.name }}/app.log
```

## `transfer.sync`

Synchronizes a local tree to a remote destination.

```yaml
- id: sync_templates
  use: transfer.sync
  with:
    src: ./files/
    dest: /opt/myapp/files/
    delete: false
```

Use `transfer.sync` for small operational trees. For very large trees, prefer a
specialized artifact or package distribution mechanism.
