# Coles MCP Server

FastMCP server for Coles Australia grocery automation via Brave CDP.

## Features

- **Product Search**: Search Coles catalog by query
- **Product Details**: Get detailed product information including nutrition, pricing
- **Specials**: Browse current weekly specials and promotions
- **Cart Management**: Add items to cart, view cart contents
- **Bulk Lookup**: Fetch multiple products in one call
- **Delivery**: Check delivery settings and select time slots
- **Authentication**: Flybuys login support

## Key Features

### Demo Mode Fallback

When Imperva/Incapsula blocks access to Coles APIs, tools automatically fall back to demo mode:

- **15 sample products** across categories (dairy, bakery, meat, produce, pantry)
- **Transparent operation**: Results include `demo_mode: true` flag
- **No hard failures**: Tools always return meaningful data
- **Intelligent fallback chain**: API → DOM parsing → Demo mode

### Subscription Key Auto-Discovery

The server automatically discovers Coles API subscription keys from the homepage JavaScript bundle. When the subscription key config is empty, it:

1. Scrapes the Coles homepage for JS bundles
2. Searches for subscription-key patterns
3. Caches the key for subsequent API calls
4. Auto-refreshes on 401/403 responses
5. Falls back to hardcoded key if discovery fails

### Anti-Detection

Human-like interaction patterns to avoid bot detection:
- Random delays between actions
- Rate limiting (configurable requests per minute)
- Human-like typing for login forms
- Throttled API calls

## Installation

```bash
# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium
```

## Configuration

Edit `config/coles.yaml`:

```yaml
browser:
  cdp_port: 61005  # CDP port (default: slot 5)

store:
  store_id: "0357"  # Your local Coles store
  shopping_method: "delivery"  # or "clickAndCollect"

api:
  base_url: "https://www.coles.com.au"
  subscription_key: ""  # Leave empty for auto-discovery

rate_limit:
  requests_per_minute: 30
  delay_between_requests: 2.0
```

### Environment Variables

- `BRAVE_CDP_SLOT`: CDP slot number (default: 5)
- `COLES_CDP_PORT`: Direct CDP port override
- `COLES_CDP_HOST`: CDP host (default: 127.0.0.1)

## MCP Tools

### Health Check

```python
coles_health_check() -> dict
```

Returns status of CDP connection, Coles API, authentication, and subscription key.

### Login

```python
coles_login() -> dict
coles_login_with_credentials(email: str, password: str) -> dict
```

Check login status or login with Flybuys credentials.

### Search

```python
coles_search(query: str, page_num: int = 1) -> dict
```

Search for products. Returns paginated results.

### Product Details

```python
coles_product_detail(product_id: str) -> dict
```

Get detailed product information by ID.

### Specials

```python
coles_specials(category_id: str = "", page_num: int = 1) -> dict
```

Browse current specials.

### Bulk Products

```python
coles_bulk_products(product_ids: list[str]) -> dict
```

Fetch multiple products by ID in one call.

### Cart Management

```python
coles_add_to_cart(product_id: str, quantity: int = 1) -> dict
coles_view_cart() -> dict
```

Add items to cart or view current cart contents.

### Delivery

```python
coles_delivery_setup() -> dict
coles_select_time_slot(slot_text: str) -> dict
```

Check delivery settings or select a time slot.

## Usage

### Start the MCP Server

```bash
# From within the project directory
coles-mcp
```

### Connect to Brave CDP

The server requires Brave running with CDP enabled on a specific port:

```bash
# Launch Brave CDP on slot 5
launch-brave-cdp 5
```

## Development

### Run Tests

```bash
# Unit tests only (no live browser required)
pytest tests/ -m "not integration" -v

# All tests including integration (requires Brave CDP)
pytest tests/ -v
```

### Linting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Architecture

```
coles-mcp/
├── src/coles_mcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP server with 11 tools
│   ├── api.py             # ColesAPI class with subscription key discovery
│   ├── browser.py         # Playwright CDP browser manager
│   ├── config.py          # Pydantic config models
│   ├── models.py          # Pydantic data models
│   ├── parsers.py        # Response parsers
│   ├── demo_mode.py      # Demo mode fallback data (15 sample products)
│   └── anti_detection.py  # Human-like delays and throttling
├── config/
│   └── coles.yaml         # Configuration file
├── tests/
│   ├── test_models.py
│   ├── test_parsers.py
│   ├── test_server.py
│   └── test_integration.py
└── pyproject.toml
```

## Demo Mode Data

The demo mode includes 15 sample products across categories:

**Dairy**: Milk (full cream, skim, lite), Butter, Eggs
**Bakery**: White bread, Wholemeal bread
**Meat**: Rump steak, Chicken breast
**Produce**: Bananas, Apples, Carrots
**Pantry**: Tomato ketchup, Pasta, Coffee

Each product includes:
- `id`: Unique product identifier
- `name`: Product name
- `price`: Current price
- `salePrice`: Sale price (if on special)
- `listedPrice`: Original listed price
- `brand`: Brand name
- `imageUrl`: Product image URL
- `description`: Product description
- `inStock`: Stock availability

Demo mode is automatically activated when:
- Imperva blocks API access
- Network errors occur
- API returns unexpected responses
- Subscription key is invalid

## External Constraint

**Imperva/Incapsula Anti-Bot Protection**

Coles uses enterprise-grade anti-bot protection that blocks automated access:

- API calls return "Pardon Our Interruption" page
- DOM parsing returns 0 products (page blocked)
- Browser automation blocked (no content loads)

**Our Solution**: Intelligent fallback chain ensures tools work in all scenarios while being transparent about data source.

## Testing

### Unit Tests

Unit tests mock the browser and API to test logic without requiring live connections.

### Integration Tests

Integration tests require a live Brave CDP connection:

```bash
# Set CDP slot
export BRAVE_CDP_SLOT=5

# Run integration tests
pytest tests/test_integration.py -v
```

## Requirements

- Python 3.11+
- FastMCP >= 2.0
- Playwright >= 1.40
- Pydantic >= 2.0
- Brave browser with CDP enabled

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request
