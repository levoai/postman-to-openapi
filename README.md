Tool to convert a Postman collection into OpenApi spec.
We use p2o npm package to do the first pass conversion from
Postman collection to OpenApi spec and then do the second
iteration to enrich the spec separately.

## Usage

```bash
# Install postman-to-openapi package
npm i postman-to-openapi -g # See https://www.npmjs.com/package/postman-to-openapi for details

# The following command generates openapi.yaml file parallel to Postman collection
./postman_collection_to_openapi.py <path to the Postman collection file>

# The following command generates the final enriched spec
./enrich_openapi_spec.py <path to the openapi.yaml file>
```
