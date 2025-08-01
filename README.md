# Taproot Assets Extension for LNbits

A powerful extension for LNbits that enables Taproot Assets functionality, allowing you to issue, manage, and transfer Bitcoin-native digital assets using the Taproot Assets Protocol.

## Features

- **Asset Management**: List and view all Taproot Assets in your node
- **Send/Receive**: Create and pay Taproot Asset invoices
- **Channel Support**: View Lightning channels with Taproot Assets
- **Balance Tracking**: Monitor asset balances across all channels
- **Real-time Updates**: WebSocket support for live balance and transaction updates

## Requirements

- LNbits instance
- Access to a Taproot Assets daemon (tapd) either:
  - Integrated within litd (recommended)
  - Running as a standalone service
- Proper credentials (TLS certificate and macaroons)

## Installation

1. Enable the extension in LNbits Admin UI or add to `LNBITS_EXTENSIONS_DEFAULT_INSTALL`
2. Configure the connection (see Configuration section)
3. Restart LNbits if necessary

## Configuration

The extension supports two connection modes:

### 1. Integrated Mode (Recommended for litd users)

If you're running litd with integrated tapd and LNbits is configured to use gRPC:

**docker-compose.yml:**
```yaml
environment:
  - LNBITS_BACKEND_WALLET_CLASS=LndGrpcWallet
  - LND_GRPC_ENDPOINT=lit
  - LND_GRPC_PORT=10009
  - LND_GRPC_CERT=/root/.lnd/tls.cert
  - LND_GRPC_MACAROON=/root/.lnd/data/chain/bitcoin/mainnet/admin.macaroon
```

**Note**: Integrated mode requires a macaroon with both LND and tapd permissions. If you encounter permission errors, use standalone mode instead.

### 2. Standalone Mode

For separate tapd instances or when LNbits uses REST:

**Option A: Environment Variables**
```yaml
environment:
  # LNbits config (can be REST or gRPC)
  - LNBITS_BACKEND_WALLET_CLASS=LndRestWallet
  - LND_REST_ENDPOINT=https://lit:8080
  - LND_REST_CERT=/root/.lnd/tls.cert
  - LND_REST_MACAROON=/root/.lnd/data/chain/bitcoin/mainnet/admin.macaroon
  
  # Taproot Assets config
  - TAPD_HOST=lit:10009
  - TAPD_TLS_CERT_PATH=/root/.lnd/tls.cert
  - TAPD_MACAROON_PATH=/root/.tapd/data/mainnet/admin.macaroon
```

**Option B: Configuration File**
1. Copy `taproot_assets.conf.example` to `taproot_assets.conf`
2. Update the settings with your paths and credentials
3. The config file takes precedence over environment variables

### Docker vs Local Paths

**Docker paths:**
- TLS cert: `/root/.lnd/tls.cert`
- LND macaroon: `/root/.lnd/data/chain/bitcoin/mainnet/admin.macaroon`
- tapd macaroon: `/root/.tapd/data/mainnet/admin.macaroon`

**Local paths:**
- TLS cert: `/home/[user]/.lnd/tls.cert`
- LND macaroon: `/home/[user]/.lnd/data/chain/bitcoin/mainnet/admin.macaroon`
- tapd macaroon: `/home/[user]/.tapd/data/mainnet/admin.macaroon`

## Connection Architecture

```
┌─────────────┐         ┌─────────────┐
│   LNbits    │         │    litd     │
│             │ REST    │             │
│  Wallet  ───┼────────►│ :8080 (LND) │
│             │         │             │
└─────────────┘         │             │
                        │             │
┌─────────────┐         │             │
│  Taproot    │ gRPC    │             │
│  Extension ─┼────────►│ :10009      │
│             │         │ (LND+tapd)  │
└─────────────┘         └─────────────┘
```

## Troubleshooting

### "Invalid macaroon" error
- In integrated mode: The LND macaroon doesn't have tapd permissions
- Solution: Use standalone mode with separate tapd credentials

### "No such file or directory" error
- Check that file paths are correct for your environment (Docker vs local)
- Ensure the tapd/lnd services are running and accessible

### Extension not loading
- Check LNbits logs: `docker logs [lnbits-container]`
- Verify all required services are running
- Ensure credentials have proper permissions

## API Endpoints

- `GET /taproot_assets/api/v1/taproot/listassets` - List all assets
- `GET /taproot_assets/api/v1/taproot/asset-balances` - Get asset balances
- `POST /taproot_assets/api/v1/taproot/createinvoice` - Create asset invoice
- `POST /taproot_assets/api/v1/taproot/payinvoice` - Pay asset invoice
- `GET /taproot_assets/api/v1/taproot/payments` - List payments
- `GET /taproot_assets/api/v1/taproot/invoices` - List invoices

## WebSocket Support

Real-time updates are available via WebSocket connections:
- Balance updates: `/api/v1/ws/taproot-assets-balances-[user-id]`
- Payment updates: `/api/v1/ws/taproot-assets-payments-[user-id]`
- Invoice updates: `/api/v1/ws/taproot-assets-invoices-[user-id]`

## Development

### Project Structure
```
taproot_assets/
├── __init__.py           # Extension initialization
├── config.json           # Extension metadata
├── views.py              # Web routes
├── views_api.py          # API endpoints
├── models.py             # Data models
├── tapd/                 # Taproot daemon integration
│   ├── taproot_node.py   # Node connection management
│   ├── taproot_assets.py # Asset operations
│   └── ...               # Other tapd modules
└── static/               # Frontend assets
```

### Adding New Features
1. Add gRPC calls in appropriate `tapd/` module
2. Create API endpoint in `views_api.py`
3. Update frontend in `static/js/`
4. Add WebSocket events if real-time updates needed

## License

This extension is part of LNbits and follows the same MIT license.