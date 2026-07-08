def paginate(items: list, page: int = 1, page_size: int = 20):
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total
