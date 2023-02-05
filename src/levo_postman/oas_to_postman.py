# Copyright 2023 Levo, Inc.
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

import os
import subprocess
import sys
import tempfile
import uuid

OPTIONS = ",".join([
    'folderStrategy=Tags',
    'includeAuthInfoInExample=false',
])


async def convert_to_postman(oas_file_path, dest_dir) -> str:
    output_path = os.path.join(dest_dir, str(uuid.uuid4()) + ".json")
    cmd = subprocess.call(
        ['openapi2postmanv2', '-s', oas_file_path, '-o', output_path, '-p', '-O', OPTIONS],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    if cmd == 0:
        # Fail if the output file is empty
        if os.stat(output_path).st_size == 0:
            raise Exception('Failed to convert OpenApi spec to Postman collection')

        return output_path
    raise Exception('Failed to convert OpenApi spec to Postman collection')
