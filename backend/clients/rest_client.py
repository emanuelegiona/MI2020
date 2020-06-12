"""
This file contains source code for handling all the REST requests involved in this project.
"""
from collections import namedtuple
import requests
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError
import typing
import json

"""
SimpleResponse object returns the outcome of a REST request, in the following format:
- code      HTTP status code (200, 404, 500, ...) for the request, or -1 in case an exception is raised
- content   response content as JSON object, or plain HTML code of the web page as a string
- headers   response headers, or None
- message   textual message associated to the previous fields, either HTTP reason ("OK", "Not Found", ...) or an exception message
"""
SimpleResponse = namedtuple("SimpleResponse", "code content headers message")


class RESTClient:
    """
    REST client implementing the HTTP methods that are required in order to work with Microsoft Azure.
    This wrapper class doesn't target any specific Azure service.
    """

    def __init__(self, debug: bool = False):
        """
        REST client constructor method.
        :param debug: if True, every REST request prints some stats to the standard output
        """
        self.__debug = debug

    def get(self, url: str, headers: dict = None, params: dict = None, expect_json: bool = True) -> SimpleResponse:
        """
        Performs an HTTP GET request.
        :param url: URL to which perform the GET request to
        :param headers: HTTP headers to be specified
        :param params: HTTP parameters to be passed in the URL querystring
        :param expect_json: if True, the client expects a JSON content response and will try to parse it, otherwise it will read plain HTML from the web page
        :return: SimpleResponse object as previously defined
        """
        code = -1
        content = None
        msg = ""
        try:
            req = requests.get(url=url,
                               headers=headers,
                               params=params)

            code = req.status_code
            msg = req.reason
            if self.__debug:
                print("GET {url} responded with {code}: {msg}".format(url=req.url,
                                                                      code=code,
                                                                      msg=msg))

            # fetch JSON in case it is expected one, otherwise retrieve response body as a string
            content = req.json() if expect_json else str(req.text)
            req.close()
        except JSONDecodeError:
            content = None
            msg = "Not a JSON"
        except ConnectionError:
            content = None
            msg = "Connection error"
        except TimeoutError:
            content = None
            msg = "Timeout"
        except RequestException:
            content = None
            msg = "General error"

        return SimpleResponse(code=code, content=content, headers=None, message=msg)

    def post(self, url: str, body: json = None, data: typing.BinaryIO = None,
             headers: dict = None, params: dict = None,
             expect_json: bool = True, response_headers: bool = False) -> SimpleResponse:
        """
        Performs an HTTP POST request.
        :param url: URL to which perform the POST request to
        :param body: JSON content to be POSTed to the URL; mutually exclusive with data
        :param data: binary content to be POSTed to the URL; mutually exclusive with body
        :param headers: HTTP headers to be specified
        :param params: HTTP parameters to be passed in the URL querystring
        :param expect_json: if True, the client expects a JSON content response and will try to parse it, otherwise it will read plain HTML from the web page
        :param response_headers: if True, the returning SimpleResponse will also contain the response headers, otherwise None
        :return: SimpleResponse object as previously defined
        """
        code = -1
        content = None
        resp_headers = None
        msg = ""
        try:
            if body is not None and data is not None:
                raise RequestException("Parameters 'body' and 'data' are mutually exclusive.")

            if body is not None:
                req = requests.post(url=url,
                                    headers=headers,
                                    params=params,
                                    json=body)
            elif data is not None:
                req = requests.post(url=url,
                                    headers=headers,
                                    params=params,
                                    data=data)
            else:
                req = requests.post(url=url,
                                    headers=headers,
                                    params=params)

            code = req.status_code
            msg = req.reason
            if self.__debug:
                print("POST {url} responded with {code}: {msg}".format(url=req.url,
                                                                       code=code,
                                                                       msg=msg))
            # fetch JSON in case it is expected one, otherwise retrieve response body as a string
            content = req.json() if expect_json else str(req.text)
            resp_headers = req.headers if response_headers else None
            req.close()
        except JSONDecodeError:
            content = None
            msg = "Not a JSON"
        except ConnectionError:
            content = None
            msg = "Connection error"
        except TimeoutError:
            content = None
            msg = "Timeout"
        except RequestException as e:
            content = None
            msg = str(e)

        return SimpleResponse(code=code, content=content, headers=resp_headers, message=msg)

    def delete(self, url: str, headers: dict = None, params: dict = None, expect_json: bool = True) -> SimpleResponse:
        """
        Performs an HTTP DELETE request.
        :param url: URL to which perform the GET request to
        :param headers: HTTP headers to be specified
        :param params: HTTP parameters to be passed in the URL querystring
        :param expect_json: if True, the client expects a JSON content response and will try to parse it, otherwise it will read plain HTML from the web page
        :return: SimpleResponse object as previously defined
        """
        code = -1
        content = None
        msg = ""
        try:
            req = requests.delete(url=url,
                                  headers=headers,
                                  params=params)

            code = req.status_code
            msg = req.reason
            if self.__debug:
                print("DELETE {url} responded with {code}: {msg}".format(url=req.url,
                                                                         code=code,
                                                                         msg=msg))
            # fetch JSON in case it is expected one, otherwise retrieve response body as a string
            content = req.json() if expect_json else str(req.text)
            req.close()
        except JSONDecodeError:
            content = None
            msg = "Not a JSON"
        except ConnectionError:
            content = None
            msg = "Connection error"
        except TimeoutError:
            content = None
            msg = "Timeout"
        except RequestException:
            content = None
            msg = "General error"

        return SimpleResponse(code=code, content=content, headers=None, message=msg)


if __name__ == "__main__":
    c = RESTClient(debug=True)
    j = c.get(url="http://httpbin.org/get")
    print(j)

    j2 = c.post(url="http://httpbin.org/post",
                body=j)
    print(j2)

    j3 = c.delete(url="http://httpbin.org/delete")
    print(j3)
