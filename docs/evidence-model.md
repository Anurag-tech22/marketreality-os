# Evidence Model

MarketReality OS separates market observations from derived findings and preserves the evidence chain between them. 

## The Evidence Object

Every deterministic calculation creates an Evidence object. The schema (`apps/api/app/models.py`) looks like this:

```python
class Evidence(BaseModel):
    evidence_id: str
    finding: str
    value: Any
    unit: str | None = None
    source_endpoint: str
    source_timestamp: str | None = None
    observation_timestamp: str
    calculation: str
    limitation: str | None = None
```

## How It Works

1. When `reality.py` calculates Top-5 Volume Concentration, it creates an `Evidence` object with ID `EV-005`, referencing `/v2/cryptocurrency/market-pairs/latest`.
2. The Evidence Investigator reads this array of objects.
3. If the Investigator makes a claim ("Volume concentration is high"), it MUST append the citation `[EV-005]`.
4. If no evidence object exists for a metric, no claim can be made.

## Important Limitations
- Evidence is only as good as the underlying CoinMarketCap data API response.

## Relevant Source Files
- `apps/api/app/models.py`
- `apps/api/app/investigator.py`
