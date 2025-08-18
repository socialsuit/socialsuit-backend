# API Documentation Examples with Project Categories

## Project Categories

The following categories are supported for projects:

- `defi` - Decentralized Finance projects
- `layer_1` - Layer 1 blockchain protocols
- `layer_2` - Layer 2 scaling solutions
- `nft` - Non-Fungible Token projects
- `gaming` - Blockchain gaming projects
- `infrastructure` - Blockchain infrastructure
- `ai` - Artificial Intelligence projects
- `dex` - Decentralized Exchanges
- `wallet` - Cryptocurrency wallets
- `tooling` - Development tools and utilities

## API Endpoints with Category Support

### Create Project

**POST** `/api/v1/projects/`

```json
{
  "name": "Uniswap",
  "slug": "uniswap",
  "website": "https://uniswap.org",
  "description": "A decentralized exchange protocol",
  "token_symbol": "UNI",
  "score": 95.5,
  "category": "dex",
  "meta_data": {
    "founded_year": 2018,
    "total_value_locked": "$4.2B"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Uniswap",
  "slug": "uniswap",
  "website": "https://uniswap.org",
  "description": "A decentralized exchange protocol",
  "token_symbol": "UNI",
  "score": 95.5,
  "category": "dex",
  "meta_data": {
    "founded_year": 2018,
    "total_value_locked": "$4.2B"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Update Project

**PUT** `/api/v1/projects/{project_id}`

```json
{
  "name": "Uniswap V3",
  "description": "Advanced AMM protocol with concentrated liquidity",
  "score": 98.0,
  "category": "dex"
}
```

### Get Projects with Category Filter

**GET** `/api/v1/projects/?category=defi&page=1&per_page=20`

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Compound",
      "slug": "compound",
      "website": "https://compound.finance",
      "description": "Decentralized lending protocol",
      "token_symbol": "COMP",
      "score": 92.3,
      "category": "defi",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "name": "Aave",
      "slug": "aave",
      "website": "https://aave.com",
      "description": "Open source liquidity protocol",
      "token_symbol": "AAVE",
      "score": 94.1,
      "category": "defi",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 20,
  "has_next": true,
  "has_prev": false
}
```

### Get Category Statistics

**GET** `/api/v1/projects/categories/stats`

**Response:**
```json
{
  "defi": 45,
  "layer_1": 12,
  "layer_2": 18,
  "nft": 23,
  "gaming": 15,
  "infrastructure": 8,
  "ai": 6,
  "dex": 19,
  "wallet": 11,
  "tooling": 14
}
```

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `category` | string | Filter by project category | `?category=defi` |
| `search` | string | Search in name and description | `?search=exchange` |
| `token_symbol` | string | Filter by token symbol | `?token_symbol=UNI` |
| `min_score` | number | Minimum project score | `?min_score=90` |
| `page` | integer | Page number (starts from 1) | `?page=2` |
| `per_page` | integer | Items per page (max 100) | `?per_page=50` |

### Combined Filtering Examples

**Get high-scoring DeFi projects:**
```
GET /api/v1/projects/?category=defi&min_score=90&per_page=10
```

**Search for DEX projects:**
```
GET /api/v1/projects/?category=dex&search=exchange
```

**Get Layer 2 projects with specific token:**
```
GET /api/v1/projects/?category=layer_2&token_symbol=MATIC
```

## Automatic Category Detection

When creating or updating projects, if no category is provided, the system will automatically detect the category based on:

1. **Keywords in project name** (e.g., "DeFi", "Exchange", "NFT")
2. **Keywords in description** (e.g., "decentralized finance", "gaming", "wallet")
3. **Website domain mapping** (e.g., uniswap.org → dex)
4. **Token symbol mapping** (e.g., UNI → dex)

### Category Detection Examples

```json
{
  "name": "SuperSwap Protocol",
  "description": "A new decentralized exchange for trading tokens"
  // Category will be automatically detected as "dex"
}
```

```json
{
  "name": "CryptoGame World",
  "description": "Play-to-earn blockchain gaming platform"
  // Category will be automatically detected as "gaming"
}
```

```json
{
  "name": "LendingDAO",
  "description": "Decentralized lending and borrowing protocol"
  // Category will be automatically detected as "defi"
}
```

## Error Responses

### Invalid Category

**Status:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "category"],
      "msg": "value is not a valid enumeration member; permitted: 'defi', 'layer_1', 'layer_2', 'nft', 'gaming', 'infrastructure', 'ai', 'dex', 'wallet', 'tooling'",
      "type": "type_error.enum",
      "ctx": {
        "enum_values": ["defi", "layer_1", "layer_2", "nft", "gaming", "infrastructure", "ai", "dex", "wallet", "tooling"]
      }
    }
  ]
}
```

### Project Not Found

**Status:** 404 Not Found

```json
{
  "detail": "Project not found"
}
```

## Migration Notes

- The `category` field is nullable for backward compatibility
- Existing projects without categories can be bulk-updated using the category detection service
- The migration includes an index on the `category` field for efficient filtering