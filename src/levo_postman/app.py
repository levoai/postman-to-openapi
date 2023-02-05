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

import asyncio
import os
import tempfile

import aiofiles as aiofiles
import uvicorn as uvicorn
from fastapi import APIRouter, Depends, FastAPI, File, UploadFile, status
from fastapi.responses import FileResponse

from levo_postman.enrich_openapi_spec import enrich_spec
from levo_postman.oas_to_postman import convert_to_postman
from levo_postman.postman_collection_to_openapi import convert_to_openapi

CHUNK_SIZE = 1024 * 1024  # = 1MB

router = APIRouter()


@router.get("/postman/health")
def health_check():
    return dict(message="I am doing good!")


async def get_temp_dir():
    tmp_dir = tempfile.TemporaryDirectory()
    try:
        yield tmp_dir.name
    finally:
        del tmp_dir


@router.post("/postman/to-oas")
async def to_oas(file: UploadFile = File(...), temp_dir=Depends(get_temp_dir)):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        tmp.write(file.file.read())
        file_path = tmp.name

        oas_file_path = await convert_to_openapi(file_path, temp_dir)
        oas_file_path = await enrich_spec(oas_file_path)
        return FileResponse(
            path=oas_file_path,
            status_code=status.HTTP_201_CREATED,
            filename=f"{file.filename}.yaml",
        )
    finally:
        tmp.close()
        os.unlink(tmp.name)


@router.post("/postman/from-oas")
async def from_oas(file: UploadFile = File(...), temp_dir=Depends(get_temp_dir)):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        tmp.write(file.file.read())
        file_path = tmp.name

        postman_file_path = await convert_to_postman(file_path, temp_dir)
        if os.stat(postman_file_path).st_size == 0:
            raise Exception('Failed to convert OpenApi spec to Postman collection')

        return FileResponse(
            path=postman_file_path,
            status_code=status.HTTP_201_CREATED,
            filename=f"collection.json",
        )
    finally:
        tmp.close()
        os.unlink(tmp.name)


async def run_server():
    config = uvicorn.Config(get_app(), host="0.0.0.0", port=8000, access_log=False)
    server = uvicorn.Server(config=config)
    # we need to override install_signal_handlers here because the existing implementation fails if
    # it isn't running in the main thread and uvicorn doesn't expose a way to configure it.
    server.install_signal_handlers = lambda: None

    assert aiofiles is not None, "'aiofiles' must be installed to use FileResponse"
    await server.serve()


def get_app():
    app = FastAPI()

    # Setup routes
    app.include_router(router)

    return app


if __name__ == "__main__":
    asyncio.run(run_server())
