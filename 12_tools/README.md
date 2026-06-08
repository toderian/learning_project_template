# 12_tools

Small vault-adjacent scripts and tiny sample data.

## Scripts

Use `12_tools/scripts/validate.sh` as the single validation entrypoint. CI uses the same wrapper.

Script logic should live in dedicated script files under `12_tools/scripts/`. Keep shell wrappers small and avoid embedding large inline validators in shell scripts or workflow YAML.

See [scripts/README.md](scripts/README.md) for usage.
