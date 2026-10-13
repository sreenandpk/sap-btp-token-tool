from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Path, Query

app = FastAPI(
    title="FastAPI + OData V2 Practice API",
    description="Practise OData V2 query options through FastAPI.",
    version="1.0.0",
)

ODATA_URL = "https://services.odata.org/V2/Northwind/Northwind.svc"

TIMEOUT = 15.0


# --------------------------------------------------
# Shared OData request helper
# --------------------------------------------------


async def call_odata(
    endpoint: str,
    params: dict | None = None,
) -> dict | list:
    """Send a request to the external OData service."""

    request_params = {
        "$format": "json",
    }

    if params:
        request_params.update(params)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{ODATA_URL}/{endpoint}",
                params=request_params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "OData service returned an error",
                "upstream_status": exc.response.status_code,
                "response": exc.response.text[:500],
            },
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the OData service",
        ) from exc


# --------------------------------------------------
# Home
# --------------------------------------------------


@app.get("/")
def home():
    return {
        "message": "FastAPI + OData V2 API is running",
        "docs": "/docs",
        "customers_endpoint": "/customers",
    }


# --------------------------------------------------
# Customers: OData V2 query options
# --------------------------------------------------


@app.get("/customers")
async def get_customers(
    filter_expr: Annotated[str | None, Query(alias="$filter")] = None,
    select: Annotated[str | None, Query(alias="$select")] = None,
    orderby: Annotated[str | None, Query(alias="$orderby")] = None,
    top: Annotated[int | None, Query(alias="$top", ge=0, le=100)] = 5,
    skip: Annotated[int | None, Query(alias="$skip", ge=0)] = None,
    expand: Annotated[str | None, Query(alias="$expand")] = None,
    inlinecount: Annotated[str | None, Query(alias="$inlinecount")] = None,
    format_: Annotated[str | None, Query(alias="$format")] = "json",
):
    """
    Supported options:
    $filter, $select, $orderby, $top, $skip,
    $expand, $inlinecount and $format.
    """

    params = {}

    options = {
        "$filter": filter_expr,
        "$select": select,
        "$orderby": orderby,
        "$top": top,
        "$skip": skip,
        "$expand": expand,
        "$inlinecount": inlinecount,
        "$format": format_,
    }

    for key, value in options.items():
        if value is not None:
            params[key] = value

    return await call_odata("Customers", params)


# --------------------------------------------------
# Get one customer by ID
# --------------------------------------------------


@app.get("/customers/{customer_id}")
async def get_customer(
    customer_id: Annotated[
        str,
        Path(min_length=1, max_length=5),
    ],
    select: Annotated[str | None, Query(alias="$select")] = None,
    expand: Annotated[str | None, Query(alias="$expand")] = None,
):
    # Escape apostrophes in OData string literals.
    safe_id = customer_id.replace("'", "''")
    endpoint = f"Customers('{safe_id}')"

    params = {}

    if select is not None:
        params["$select"] = select

    if expand is not None:
        params["$expand"] = expand

    return await call_odata(endpoint, params)


# --------------------------------------------------
# Count customers
# --------------------------------------------------


@app.get("/customers/count")
async def count_customers(
    filter_expr: Annotated[str | None, Query(alias="$filter")] = None,
):
    # OData V2 exposes counts through the /$count path.
    params = {}

    if filter_expr is not None:
        params["$filter"] = filter_expr

    result = await call_odata("Customers/$count", params)

    return {
        "count": result,
    }
