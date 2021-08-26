import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    now_year = dt.datetime.now().year
    return {'year': now_year}
