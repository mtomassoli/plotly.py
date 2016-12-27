from __future__ import absolute_import

import base64

import requests
import six
from requests.exceptions import RequestException

from plotly import config, exceptions


def validate_response(response):
    """
    Raise a helpful PlotlyRequestError for failed requests.

    :param (requests.Response) response: A Response object from an api request.
    :raises: (PlotlyRequestError) If the request failed for any reason.
    :returns: (None)

    """
    if response.ok:
        return

    content = response.content
    status_code = response.status_code
    try:
        parsed_content = response.json()
    except ValueError:
        message = content if content else 'No Content'
        raise exceptions.PlotlyRequestError(message, status_code, content)

    message = ''
    if isinstance(parsed_content, dict):
        error = parsed_content.get('error')
        if error:
            message = error
    if not message:
        message = content if content else 'No Content'

    raise exceptions.PlotlyRequestError(message, status_code, content)


def basic_auth(username, password):
    """
    Creates the basic auth value to be used in an authorization header.

    :param (str) username: A Plotly username.
    :param (str) password: The password for the given Plotly username.
    :returns: (str) An 'authorization' header for use in a request header.

    """
    auth = '{}:{}'.format(username, password)
    encoded_auth = base64.b64encode(six.b(auth))
    return six.b('Basic ') + encoded_auth


def get_headers():
    """
    Using session credentials/config, get headers for a V2 API request.

    Users may have their own proxy layer and so we free up the `authorization`
    header for this purpose (instead adding the user authorization in a new
    `plotly-authorization` header). See pull #239.

    :returns: (dict) Headers to add to a requests.request call.

    """
    headers = {'content-type': 'application/json'}
    creds = config.get_credentials()
    proxy_auth = basic_auth(creds['proxy_username'], creds['proxy_password'])

    if config.get_config()['plotly_proxy_authorization']:
        headers['authorization'] = proxy_auth

    return headers


def request(method, url, **kwargs):
    """
    Central place to make any v1 api request.

    :param (str) method: The request method ('get', 'put', 'delete', ...).
    :param (str) url: The full api url to make the request to.
    :param kwargs: These are passed along to requests.
    :return: (requests.Response) The response directly from requests.

    """
    if kwargs.get('json', None) is not None:
        # See plotly.api.v2.utils.request for examples on how to do this.
        raise exceptions.PlotlyError('V1 API does not handle arbitrary json.')
    kwargs['headers'] = dict(kwargs.get('headers', {}), **get_headers())
    try:
        response = requests.request(method, url, **kwargs)
    except RequestException as e:
        message = getattr(e, 'message', 'No message')
        response = getattr(e, 'response', None)
        status_code = response.status_code if response else None
        content = response.content if response else 'No content'
        raise exceptions.PlotlyRequestError(message, status_code, content)
    validate_response(response)
    return response
