<!-- 🚫 AI_MODIFY_PROHIBITED -->
<!-- This directory contains auto-generated API documentation -->

# API Documentation Directory

This directory contains automatically generated API documentation. 

## 🚫 Protection Level: AUTO-GENERATED

**Do not manually edit files in this directory.** All documentation here is generated from source code and OpenAPI specifications.

## Directory Structure

- `openapi.json` - OpenAPI/Swagger specification (auto-generated)
- `generated/` - Auto-generated documentation files
  - `endpoints.md` - API endpoint documentation
  - `schemas.md` - Data schema documentation
  - `examples.md` - API usage examples

## Generation Process

API documentation is generated using:
1. FastAPI's automatic OpenAPI schema generation
2. Custom documentation generators in `/scripts/generate-docs.py`

To regenerate documentation:
```bash
make generate-api-docs
```

## Viewing Documentation

- **Swagger UI**: Available at `http://localhost:8000/docs` when API server is running
- **ReDoc**: Available at `http://localhost:8000/redoc` when API server is running
- **Static Files**: Markdown files in `generated/` directory

## Customization

To customize the generated documentation:
1. Update docstrings in source code
2. Modify OpenAPI metadata in `api/main.py`
3. Update generation scripts in `/scripts/`

**Never edit the generated files directly** - your changes will be lost on the next generation.