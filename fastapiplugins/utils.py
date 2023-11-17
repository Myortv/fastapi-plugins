from fastapi import HTTPException


def resolve_detail_conflict(e):
    try:
        detail = e.detail
    except:
        detail = e.__str__()
    finally:
        return detail


def raise_exception(e):
    try:
        status_code = e.status_code
    except:  # ADD: exception
        status_code = 500

    detail = resolve_detail_conflict(e)
    raise HTTPException(
        status_code=status_code, 
        detail=detail, 
    )

