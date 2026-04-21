
```markdown id="7x3p6k"
# USD Price Tool

## Purpose

The USD price tool is responsible for retrieving the current USD exchange price from an external API.

This tool should not know HTTP details directly.  
The external API must be hidden behind a provider adapter.

---

## Tool Name

`usd_price_tool`

---

## Responsibilities

The USD price tool should:

- validate the requested action
- call the FX quote service
- return a normalized quote response

It should **not**:

- perform raw HTTP logic inline
- know API authentication details
- know caching implementation details
- contain orchestration logic

---

## Supported Actions

- `get_price`

---

## Input Schema

```python id="vaxnso"
{
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["get_price"]
        }
    },
    "required": ["action"]
}