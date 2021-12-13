#!/usr/bin/env python3
"""
This script is used to enrich the OpenAPI spec that's generated from the Postman collection
and also split the spec into multiple files based on given prefix.

Here are the things that we take care of:
 - Add path parameters to the paths if we find them missing
 - Replace undefined response status codes with 200
 - Remove content-type parameter because it's not needed

"""
import os
import re
import sys
import uuid
import yaml
 
 
def is_valid_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def add_path_param(spec, path, part, name, schema):
    for method in spec['paths'][path]:
      endpoint_spec = None
      endpoint_spec = spec['paths'][path][method]

      if 'parameters' not in endpoint_spec:
        endpoint_spec['parameters'] = []

      if part not in endpoint_spec['parameters']:
        print("Adding path parameter: " + name + " to path: " + method + " " + path)
        print("Schema: " + str(schema))
        endpoint_spec['parameters'].append({
                'name': name,
                'in': 'path',
                'example': part,
                'required': True,
                'schema': schema
              })
      
def enrich_spec(spec_file_path, prefix):
  """Main entry method.
  """   
  with open(spec_file_path) as f:
      # use safe_load instead load
      spec = yaml.safe_load(f)

      new_paths = {}
      old_paths = []
      initial_count = len(spec['paths'])
      for path in spec['paths']:
        if prefix and not path.startswith("/" + prefix):
          continue

        old_paths.append(path)
        parts, new_parts = convert_path(spec, path)

        # Now replace the path with parameterized path
        new_path = ("/" + "/".join(new_parts)) if bool(parts) else path

        # There are some undefined response status codes. Replace them.
        endpoint_spec = spec['paths'][path]
        fix_undefined_response_code(endpoint_spec)
        remove_content_type_param(endpoint_spec)
        if new_parts:
          add_missing_path_params(endpoint_spec, new_parts)
        new_paths[new_path] = endpoint_spec
        
      spec['paths'] = new_paths

      base_name = os.path.basename(spec_file_path)
      file_name = prefix + '_service.yaml' if prefix else ("enriched_" + base_name)
      with open(os.path.join(os.path.dirname(spec_file_path), file_name), 'w') as outfile:
        yaml.dump(spec, outfile, default_flow_style=False)
      print('{}/{} endpoints enriched.'.format(len(spec['paths']), initial_count))

      # TODO: we might need to edit the Auth scheme.


def add_missing_path_params(endpoint_spec, new_parts):
    for method in endpoint_spec:
      if 'parameters' not in endpoint_spec[method]:
        endpoint_spec[method]['parameters'] = []

      for part in new_parts:
        is_param_present = False
        stripped_part = part.replace("{", "").replace("}", "")
        for param in endpoint_spec[method]['parameters']:
          if param['in'] == 'path' and param['name'] == stripped_part:
            is_param_present = True
            break
        if not is_param_present and part.startswith("{"):
          print("Adding missing path parameter: " + part)
          endpoint_spec[method]['parameters'].append({
            'name': stripped_part,
            'in': 'path',
            'required': True,
            'schema': {
              'type': 'string'
            }
          })


def remove_content_type_param(endpoint_spec):
    for method in endpoint_spec:
      if 'parameters' in endpoint_spec[method]:
        content_type = None
        schema = None
        for param in endpoint_spec[method]['parameters']:
          if param['in'] == 'header' and param['name'].lower() == 'content-type':
            print("Removing content-type parameter")
            content_type = param['example'] if 'example' in param else None
            schema = param['schema'] if 'schema' in param else None
            endpoint_spec[method]['parameters'].remove(param)

        if len(endpoint_spec[method]['parameters']) == 0:
          del endpoint_spec[method]['parameters']

        if content_type and schema and method in ['post', 'put']:
          endpoint_spec[method]['requestBody'] = {
            'content': {
              content_type: {
                'schema': schema
              }
            }
          }



def fix_undefined_response_code(endpoint_spec):
    for method in endpoint_spec:
      if 'undefined' in endpoint_spec[method]['responses']:
        print("Replacing undefined response status code with 200")
        endpoint_spec[method]['responses']['200'] = endpoint_spec[method]['responses']['undefined']
        endpoint_spec[method]['responses']['200']['description'] = 'OK'
        del endpoint_spec[method]['responses']['undefined']


def convert_path(spec, path):
    parts = path.strip("/").split('/')
    new_parts = []
    params = []
    for part in parts:
      # if the part is a number, then it is a path parameter
      type = None
      format = None
      if part.isdigit():
        type = 'integer'
        format = 'int64'
      elif is_valid_uuid(part):
        type = 'string'
        format = 'uuid'
      else:
        new_parts.append(part)
        continue

      params.append(part)

      # if the number is not in the list of path parameters, then add it
      index = parts.index(part) - 1

      # How we name the param depending on if it's the first part of the path and if its previous
      # part was also a param or not.
      name = parts[index] + "_id" if index >= 0 and parts[index] not in params else "id"
      schema = {'type': type}
      if format:
        schema['format'] = format
      add_path_param(spec, path, part, name, schema)
      new_parts.append("{" + name + "}")
    return parts, new_parts

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: {} <postman collection file>'.format(sys.argv[0]))
        sys.exit(1)

    # Exit if the file doesn't exist
    if not os.path.isfile(sys.argv[1]):
        print('File {} does not exist'.format(sys.argv[1]))
        sys.exit(1)
    
    prefix = sys.argv[2] if len(sys.argv) > 2 else ''
    enrich_spec(sys.argv[1], prefix=prefix)
