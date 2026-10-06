from django.core.paginator import Paginator

ROWS_PER_PAGE = 10
PAGE_WINDOW = 3


def paginate(queryset, page_number, per_page=ROWS_PER_PAGE):
    """
    Return the requested page of a queryset.

    The page carries `page_window`, the run of page numbers to show as links
    (PAGE_WINDOW pages around the current one).
    """
    page_obj = Paginator(queryset, per_page).get_page(page_number)

    last_page = page_obj.paginator.num_pages
    start = max(1, min(page_obj.number - PAGE_WINDOW // 2, last_page - PAGE_WINDOW + 1))
    end = min(last_page, start + PAGE_WINDOW - 1)
    page_obj.page_window = range(start, end + 1)

    return page_obj
