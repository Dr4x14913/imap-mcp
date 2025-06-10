# Imap mcp server

A simple imap mcp server for browsing your emails. It is build using [fastmcp](https://github.com/jlowin/fastmcp)
.

## Config
```json
{
  "mcpServers": {
    "imap-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/imap-mcp",
        "run",
        "server.py"
      ],
      "env": {
        "IMAP_USER": "USER",
        "IMAP_PASSWORD": "PASSWORD",
        "IMAP_SERVER": "server dns or ip",
      }
    }
  }
}
```