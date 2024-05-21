# httpkit
A requests + pydantic based framework to save you the trouble

## Installation

Add **apikit** to the project dependencies using the **poetry add** command, or install it with **pip install**. Specify the tag version if necessary.

```shell
poetry add git+https://github.com/Arbeit-Studio/apikit.git@v0.1.2
```

To install using **pip**, just change the poetry command to the pip one.

```shell
pip install git+https://github.com/Arbeit-Studio/apikit.git@v0.1.2
```

## Specifying the Gateway

The component to declare a gateway is the `DefaultHTTPRequestGateway`.

The component is called **Gateway** to denote a passthrough gate where we'll have an optional check-in for consistency on both ends when making a request and when receiving the response.

In other words, it's a declarative way to define a request, specifying its HTTP verb, URL, adapters, and expected data models.

### Example

In this example, we declare a **POST** request to [httpbin.org](https://httpbin.org).

The data expected to be sent as the request body is declared in the `RequestBody` class. You can call it anything; `RequestBody` is just the name I chose for the example.

The data expected to be present in the response body is declared in the `ResponseBody` class (again, you may call it anything).

The **httpbin.org** tool returns the same payload we send to it in the **json** attribute of the response body. That's why our `ResponseBody` defines the json attribute. You'll see this in a moment. For more details on how to use httpbin.org for your tests, check out its documentation.

```python
from apikit.protocols import HTTPMethod
from apikit.session import DefaultHttpSession
from apikit.default import (DefaultHTTPRequestAdapter, DefaultHTTPRequestGateway, DefaultHTTPResponseAdapter)
from pydantic import BaseModel


class RequestBody(BaseModel):
    foo: str
    bar: str


class ResponseBody(BaseModel):
    json: dict


gateway = DefaultHTTPRequestGateway(
    session=DefaultHttpSession(),
    url="https://httpbin.org/post",
    method=HTTPMethod.POST,
    request_adapter=DefaultHTTPRequestAdapter(model=RequestBody),
    response_adapter=DefaultHTTPResponseAdapter(model=ResponseBody)
)
```

### Making the Request

To execute the request, you just need to call the gateway, passing the request parameters if there are any.

```python
gateway(RequestBody(foo="foo", bar="bar"))
```

If you define the response model, the return will be validated, and the response model will be instantiated with the data.

```python
ResponseBody(json={'bar': 'bar', 'foo': 'foo'})
```

## Easier Declaration with HTTPGatewaySpec

The easiest way to define a Gateway is using **HTTPGatewaySpec** [descriptor](https://docs.python.org/3.10/howto/descriptor.html). Under the hood, the Spec will create a Gateway based on the details you've declared and bind it to your class attribute.

Modeling the same example from above using the **HTTPGatewaySpec** is simpler because it already uses the default adapters. If you do not override them, then you just need to specify the *url*, *method*, *request_model*, and *response_model*.

```python
from pydantic import BaseModel
from apikit.specs import HTTPGatewaySpec
from apikit.protocols import HTTPMethod

class RequestBody(BaseModel):
    foo: str
    bar: str


class ResponseBody(BaseModel):
    json: dict


class HttpBinOrgClient:

    post_foo_bar = HTTPGatewaySpec(
        url="https://httpbin.org/post",
        method=HTTPMethod.POST,
        request_model=RequestBody,
        response_model=ResponseBody,
    )
```

So, you can make the request by calling the client object attribute.

```python
client = HttpBinOrgClient()

client.post_foo_bar(RequestBody(foo="foo", bar="bar"))
```

And get the same response as before.

```python
ResponseBody(json={'bar': 'bar', 'foo': 'foo'})
```

You can also customize and reuse the Spec by overriding its class attributes. Then, every gateway created by that same Spec will have the same attributes, and you won't need to provide them every time.

```python
from apikit.specs import HTTPGatewaySpec
from apikit.protocols import HTTPMethod

class MyCustomResponseAdapter(DefaultHTTPResponseAdapter):

    def adapt(self, response):
        return response.json()


class MyAPIGatewayGETSpec(HTTPGatewaySpec, base_url="https://httpbin.org"):
    method = HTTPMethod.POST
    response_adapter = MyCustomResponseAdapter


class HttpBinOrgClient:

    post_foo_bar = MyAPIGatewayGETSpec(
        url="/post",
        request_model=RequestBody,
        response_model=ResponseBody,
    )
```

## Data Validation, Parsing, and Serialization

The heavy lifting of validation, parsing, and serialization is done by the Pydantic models you define as *request_model* and *response_model*.

Internally, the default adapters create a [TypeAdapter](https://docs.pydantic.dev/latest/api/type_adapter/) based on the provided models. They use it to validate the request data and serialize it, and also validate the response data and parse it.

## Simpler Models

If, for some reason, you don't want to implement Pydantic's BaseModels, you can also use regular dataclasses and TypedDict as models for your data if it's simple enough to be described that way.

```python
from dataclasses import dataclass
from apikit.specs import HTTPGatewaySpec
from apikit.protocols import HTTPMethod

@dataclass
class RequestBody:
    foo: str
    bar: str


@dataclass
class ResponseBody:
    json: dict


class HttpBinOrgClient:

    post_foo_bar = HTTPGatewaySpec(
        url="https://httpbin.org/post",
        method=HTTPMethod.POST,
        request_model=RequestBody,
        response_model=ResponseBody,
    )
```

