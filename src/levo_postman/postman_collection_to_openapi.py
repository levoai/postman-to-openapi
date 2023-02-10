#!/usr/bin/env python3

# Copyright 2022 Levo, Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
import tempfile
import uuid

OPTIONS_FILE_PATH = os.getenv("OPTIONS_FILE", "options.json")


def _flatten_items(items):
    """
    Flatten a list of items.
    """
    flat_list = []
    for it in items:
        result = _flatten_items(it['item']) if 'item' in it else [it]
        for new_item in result:
            new_item['tags'] = new_item['tags'] + [it['name']] if 'tags' in new_item else [it['name']]
        flat_list.extend(result)
    return flat_list


def _convert_to_openapi(postman_collection, dest_dir=None):
    # Write to a temp file if dest_dir is not specified
    if dest_dir is None:
        dest_dir = tempfile.mkdtemp()

    # write the flattened collection to a file
    with tempfile.NamedTemporaryFile(mode="w+") as tmp:
        json.dump(postman_collection, tmp, indent=4)
        tmp.seek(0)

        # Replace the "{{protocol}}://{{host}}:{{port}}" pattern in every line of the collection with
        # "https://example.com"
        # This is to make sure the OpenApi spec doesn't have host and port as params.
        with open(tmp.name) as tmp_file:
            collection = tmp_file.read()
            collection = collection.replace('{{protocol}}://{{host}}:{{port}}', 'https://example.com')
            with tempfile.NamedTemporaryFile(mode="w+") as tmp2:
                tmp2.write(collection)
                tmp2.seek(0)

                # Generate a temp file
                oas_path = os.path.join(dest_dir, str(uuid.uuid4()))
                cmd = subprocess.call(
                    ['p2o', tmp2.name, '-f', oas_path, '-o', OPTIONS_FILE_PATH],
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )

                # Print the output
                if cmd == 0:
                    return oas_path
                raise Exception('Failed to convert to OpenApi spec.')


async def convert_to_openapi(postman_collection_file, dest_dir=None) -> str:
    with open(postman_collection_file) as f:
        postman_col = json.load(f)

        # Postman collection might have nested items. Flatten them.
        postman_col['item'] = _flatten_items(postman_col['item']) if 'item' in postman_col else []

        # Try converting every item to OpenApi spec, to see if any endpoints have issue in converting.
        initial_count = len(postman_col['item'])
        print('Converting {} items.'.format(initial_count))
        new_items = []
        for item in postman_col['item']:
            if _convert_to_openapi({"item": [item], "info": postman_col['info']}):
                new_items.append(item)

        # Finally, convert the collection with all good items into OpenApi spec.
        oas_file_path = _convert_to_openapi({"item": new_items, "info": postman_col['info']}, dest_dir)
        print('{}/{} items converted to OpenApi spec.'.format(len(new_items), initial_count))
        return oas_file_path


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: {} <postman collection file>'.format(sys.argv[0]))
        sys.exit(1)

    # Exit if the file doesn't exist
    if not os.path.isfile(sys.argv[1]):
        print('File {} does not exist'.format(sys.argv[1]))
        sys.exit(1)

    convert_to_openapi(sys.argv[1], os.path.dirname(sys.argv[1]))
