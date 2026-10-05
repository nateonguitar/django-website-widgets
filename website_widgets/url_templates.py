from urllib.parse import quote

from django.urls import NoReverseMatch, get_resolver, get_script_prefix, get_urlconf
from django.urls.resolvers import get_ns_resolver
from django.utils.http import RFC3986_SUBDELIMS, escape_leading_slashes


def reverse_template(viewname: str, paramnames: list[str] | None = None) -> str:
    """
    Reverses a URL name into a template whose parameters are `{name}` placeholders, for the
    frontend to fill in:

        reverse_template('post_comment_detail')
        # '/posts/{post_id}/comments/{comment_id}'

    The placeholder names are the route's own parameter names. `paramnames` renames them, in the
    order they appear in the route, which an unnamed `re_path()` group needs. A URL with no
    parameters comes back as `reverse()` returns it.
    """
    *namespaces, view = viewname.split(':')
    resolver = get_resolver(get_urlconf())
    namespace_prefix = ''
    namespace_converters = {}
    # Mirrors the namespace walk in Django's reverse(), minus current_app, so an app namespace
    # resolves to its default instance.
    for namespace in namespaces:
        instance_namespaces = resolver.app_dict.get(namespace, [namespace])
        if namespace not in instance_namespaces:
            namespace = instance_namespaces[0]
        if namespace not in resolver.namespace_dict:
            raise NoReverseMatch(f"'{namespace}' is not a registered namespace in '{viewname}'")
        extra_prefix, resolver = resolver.namespace_dict[namespace]
        namespace_prefix += extra_prefix
        namespace_converters.update(resolver.pattern.converters)
    if namespace_prefix:
        resolver = get_ns_resolver(
            namespace_prefix,
            resolver,
            tuple(namespace_converters.items()))

    candidates = [
        (result, params)
        for possibility, _pattern, _defaults, _converters in resolver.reverse_dict.getlist(view)
        for result, params in possibility
    ]
    if paramnames is not None:
        candidates = [
            (result, params)
            for result, params in candidates
            if len(params) == len(paramnames)
        ]
    if not candidates:
        raise NoReverseMatch(f"Reverse for '{viewname}' with parameters {paramnames} not found.")
    distinct_params = {tuple(params) for _result, params in candidates}
    if paramnames is None and len(distinct_params) > 1:
        raise ValueError(
            f"'{viewname}' matches routes with different parameters {sorted(distinct_params)}; "
            f"pass paramnames to choose one.")

    # Unlike reverse(), converters and the route's regex are skipped: no placeholder would pass them.
    result, params = candidates[0]
    placeholder_names = paramnames if paramnames is not None else params
    placeholders = {param: '{' + name + '}' for param, name in zip(params, placeholder_names)}
    url_with_prefix = get_script_prefix().replace('%', '%%') + result
    url = quote(url_with_prefix % placeholders, safe=RFC3986_SUBDELIMS + '/~:@{}')
    return escape_leading_slashes(url)
