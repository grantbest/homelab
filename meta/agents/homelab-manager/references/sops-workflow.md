# SOPS Secret Workflow

## Commands
1. **Decrypt:** `sops --decrypt --in-place .env`
2. **Edit:** Modify the decrypted `.env` file.
3. **Encrypt:** `sops --encrypt --in-place .env`

## Security Guardrails
- Never commit a decrypted `.env` file.
- Verify `sops_version` exists in the file before committing.
