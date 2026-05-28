# linux-pkg

Personal RPM packages for Fedora Linux, published at `https://repo.devtools.site`.

## Setup

```bash
sudo dnf install https://repo.devtools.site/rpm/noarch/kter-release-1-1.fc42.noarch.rpm
```

## Available packages

| Package | Description |
|---|---|
| `auto-brightness` | Adjust screen brightness based on webcam ambient light |
| `kter-release` | Repository configuration (install this first) |

## Usage

```bash
sudo dnf install auto-brightness
```

After installation, the `auto-brightness.timer` systemd user unit is automatically enabled and started.

## Development

Sync sources from linux-config:

```bash
make sync-sources
```

Build RPM locally (requires `rpmdevtools`):

```bash
make build-local
```

## Documentation

Detailed specs and operations are documented in `docs/` (Japanese):

- [docs/architecture.md](docs/architecture.md) — System overview and data flow
- [docs/operations.md](docs/operations.md) — Day-to-day operations
- [docs/infrastructure.md](docs/infrastructure.md) — AWS resource details and rebuild guide
- [docs/troubleshooting.md](docs/troubleshooting.md) — Known issues and fixes
- [docs/design-decisions.md](docs/design-decisions.md) — Why things are the way they are
- [docs/packages/auto-brightness.md](docs/packages/auto-brightness.md) — Package internals
