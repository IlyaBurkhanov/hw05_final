from django.urls import reverse


def get_use_urls(obj, url_name):
    return {
        url: reverse(url, kwargs={slug: getattr(obj, slug)
                                  for slug in slugs.get('slugs', [])})
        for url, slugs in url_name.items()}
