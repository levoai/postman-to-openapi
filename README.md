# Postman to OpenAPI
![Postman-to-OpenAPI](./assets/postman-to-openapi.svg)

## Synopsis
Postman collections are ubiquitous and invaluable for the functional testing of APIs. 

However specialized API tests such as *API Contract Testing*, and *API Security Testing* require proper OpenAPI Specifications as inputs.

This tools converts Postman collections to full featured OpenAPI v3 Specifications.

## Usage

1. Install `postman-to-openapi` NPM package
```bash 
# See https://www.npmjs.com/package postman-to-openapi for details
sudo npm i postman-to-openapi -g
```

2. Install `json-schema` python package
```bash
pip install genson
```

3. Generate the OpenAPI YAML
```bash
./postman_collection_to_openapi.py <path to the Postman Collection file>
```

> The OpenAPI file will be saved to the same directory as the specified Postman Collection.

4. Generate an enriched OpenAPI Specification

```bash
./enrich_openapi_spec.py <path to the openapi.yaml file>
```

> The enriched OpenAPI file will be saved to the same directory as the specified `openapi.yaml`.

- Enrichment does the following:
   - Split the specification into multiple files based on given prefix
   - Add path parameters to the paths if missing
   - Replace undefined response status codes with 200
   - Remove redundant `content-type` parameters


## Examples

The `./examples` directory has examples of OpenAPI Specifications generated from Postman Collections (for a couple of well know APIs  - [GitLab](https://about.gitlab.com/), and [GoodBank](https://www.postman.com/studentconnects/workspace/learning-apis/documentation/4368270-0efa0ab1-a280-488d-900f-28d724f12635)).