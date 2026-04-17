from fastapi import HTTPException, status


def require_data(response, detail: str = "Resource not found"):
    """Raise 404 if response has no data, otherwise return first item."""
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return response.data[0]
