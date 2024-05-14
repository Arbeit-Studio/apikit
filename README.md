# httpkit
A requests + pydantic based fremawork to save you the trouble

## Installation

Add the **apikit** to the project dependencies using the **poetry add** command, or installing it with **pip install**. Specify the tag version if necessary.

Installing the lastest version.

```shell
poetry add poetry add git+https://github.com/Arbeit-Studio/apikit.git
```

Especifying the version using git tags.

```shell
poetry add poetry add git+https://github.com/Arbeit-Studio/apikit.git@v0.1.2
```
To install using **pip**, the way you specify the repository is the same, just change the poetry command to the pip one.

```shell
pip install git+https://github.com/Arbeit-Studio/apikit.git@v0.1.2"
```

## Specifying the Gateway

O Componente base para declarar um gateway é o `DefaultHTTPRequestGateway`.

The component is called **Gateway** to denote a passthought gate where we'll have a optional check-in for concistency on both ends, when making a request and when receiving the response.

In other words, it's a declarative way to define a request, specifying its HTTP verb, url, adapters, and expected data models.


### Example

On this example we declare a **POST** request to the [httpbin.org](https://httpbin.org). 

The data expected to be sent as the request body are declared on the `RequestBody` class. You can call it anything RequestBody is just the name I choose for the example.

The data expected to be presente in the response body are declared on the `ResponseBody` class (Again, you may call it anithing). 

The **httpbin.org** tool returns the same payload we send to it on the **json** atribute from the response body. That's why our `ResponseBody` defines the json attribute. You'll see in a moment. For more details on how to use httpbin.org for your tests check out it's documentation.

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
    http_session=DefaultHttpSession(),
    url="https://httpbin.org/post",
    method=HTTPMethod.POST,
    request_adapter=DefaultHTTPRequestAdapter(model=RequestBody),
    response_adapter=DefaultHTTPResponseAdapter(model=ResponseBody)

)
```

### Making the Request
To execute the request, you just need to call the gateway passing the request params if there is any.

```python
gateway(RequestBody(foo="foo", bar="bar"))
```

If you define the response model, the return will be validated and the response model will be instantiated with the data.

```python
ResponseBody(json={'bar': 'bar', 'foo': 'foo'})
```
